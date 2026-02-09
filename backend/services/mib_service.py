import os
import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from pysnmp.smi import builder, view, compiler
from pysnmp.proto.api import v2c
from core.config import settings

logger = logging.getLogger(__name__)

class MibDependency:
    """Represents a MIB import dependency"""
    def __init__(self, name: str, required_by: str):
        self.name = name
        self.required_by = required_by
    
    def to_dict(self):
        return {"name": self.name, "required_by": self.required_by}

class MibInfo:
    """Metadata about a loaded MIB"""
    def __init__(self, name: str, file_path: str, status: str = "loaded"):
        self.name = name
        self.file_path = file_path
        self.status = status
        self.imports: List[str] = []
        self.objects_count = 0
        self.traps_count = 0
        self.error_message: Optional[str] = None
    
    def to_dict(self):
        return {
            "name": self.name,
            "file": os.path.basename(self.file_path),
            "status": self.status,
            "imports": self.imports,
            "objects": self.objects_count,
            "traps": self.traps_count,
            "error": self.error_message
        }
    
@dataclass
class OidNode:
    """Represents a node in the OID tree"""
    oid: tuple
    name: str
    module: str
    node_type: str = ""
    syntax: str = ""
    access: str = ""
    status: str = ""
    description: str = ""
    parent_oid: Optional[tuple] = None
    children: List[tuple] = None
    indexes: List[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.indexes is None:
            self.indexes = []
    
    @property
    def full_name(self):
        return f"{self.module}::{self.name}"
    
    @property
    def oid_str(self):
        return ".".join(map(str, self.oid))
    
    def to_dict(self):
        return {
            "oid": self.oid_str,
            "name": self.name,
            "full_name": self.full_name,
            "module": self.module,
            "parent": ".".join(map(str, self.parent_oid)) if self.parent_oid else None,
            "children": [".".join(map(str, c)) for c in self.children],
            "type": self.node_type,
            "syntax": self.syntax,
            "access": self.access,
            "status": self.status,
            "description": self.description,
            "indexes": self.indexes,
            "has_children": len(self.children) > 0
        }

class MibService:
    """
    Singleton MIB manager with dependency tracking and hot-reload support.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.mib_builder = builder.MibBuilder()
        self.mib_view = view.MibViewController(self.mib_builder)
        self.loaded_mibs: Dict[str, MibInfo] = {}
        self.failed_mibs: Dict[str, MibInfo] = {}

        # NEW: Tree and search structures
        self.oid_tree: Dict[tuple, OidNode] = {}
        self.oid_index: Dict[str, tuple] = {}
        self.name_index: Dict[str, tuple] = {}
        self.search_index: Dict[str, Set[tuple]] = {}
        self.module_roots: Dict[str, List[tuple]] = {}  # module_name -> [root OIDs]
        
        self._configure_sources()
        self._load_all_mibs()
        
        self._initialized = True
        logger.info(f"MibService initialized: {len(self.loaded_mibs)} MIBs loaded")
    
    def _configure_sources(self):
        """Configure MIB search paths"""
        sources = [
            f'file://{os.path.abspath(settings.MIB_DIR)}',
            'file:///usr/share/snmp/mibs',
            'file:///usr/share/snmp/mibs/ietf',
            'file:///usr/share/snmp/mibs/iana',
            'https://mibs.pysnmp.com/asn1/@mib@'
        ]
        
        compiler.add_mib_compiler(self.mib_builder, sources=sources)
        logger.debug(f"MIB sources configured: {sources}")
    
    def _load_all_mibs(self):
        """Load all MIBs from the MIB directory"""
        if not os.path.exists(settings.MIB_DIR):
            logger.warning(f"MIB directory not found: {settings.MIB_DIR}")
            return
        
        mib_files = self._discover_mib_files()
        logger.info(f"Found {len(mib_files)} MIB files")
        
        for mib_name, file_path in mib_files.items():
            self._load_single_mib(mib_name, file_path)
        
        self._update_statistics()
        self._build_tree_structure()  # NEW: Build tree after loading

    
    def _discover_mib_files(self) -> Dict[str, str]:
        """Scan MIB directory and return {mib_name: file_path}"""
        mib_files = {}
        
        for file_name in os.listdir(settings.MIB_DIR):
            if file_name.endswith(('.mib', '.txt', '.my')):
                mib_name = file_name.rsplit('.', 1)[0]
                file_path = os.path.join(settings.MIB_DIR, file_name)
                mib_files[mib_name] = file_path
        
        return mib_files
    
    def _load_single_mib(self, mib_name: str, file_path: str):
        """Load a single MIB and track its status"""
        try:
            self.mib_builder.load_modules(mib_name)
            
            mib_info = MibInfo(mib_name, file_path, status="loaded")
            mib_info.imports = self._extract_imports(file_path)
            
            self.loaded_mibs[mib_name] = mib_info
            logger.debug(f"✓ Loaded MIB: {mib_name}")
            
        except Exception as e:
            mib_info = MibInfo(mib_name, file_path, status="error")
            mib_info.error_message = str(e)
            
            if "Cannot find" in str(e) or "No module named" in str(e):
                mib_info.status = "missing_deps"
            
            self.failed_mibs[mib_name] = mib_info
            logger.warning(f"✗ Failed to load MIB {mib_name}: {e}")
    
    def _extract_imports(self, file_path: str) -> List[str]:
        """Parse MIB file to extract IMPORTS"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                import_match = re.search(r'IMPORTS\s+(.*?);', content, re.DOTALL | re.IGNORECASE)
                
                if import_match:
                    import_block = import_match.group(1)
                    from_matches = re.findall(r'FROM\s+([A-Za-z0-9\-]+)', import_block)
                    imports = list(set(from_matches))
        
        except Exception as e:
            logger.debug(f"Could not parse imports from {file_path}: {e}")
        
        return imports
    
    def _update_statistics(self):
        """Count objects and traps in loaded MIBs"""
        for module_name, symbols in self.mib_builder.mibSymbols.items():
            if module_name not in self.loaded_mibs:
                continue
            
            mib_info = self.loaded_mibs[module_name]
            
            # Reset counts
            mib_info.objects_count = 0
            mib_info.traps_count = 0
            
            for symbol_name, symbol_obj in symbols.items():
                class_name = symbol_obj.__class__.__name__
                
                if class_name == 'NotificationType':
                    mib_info.traps_count += 1
                    logger.debug(f"Found trap: {module_name}::{symbol_name}")
                elif class_name in ['MibScalar', 'MibTableColumn']:
                    mib_info.objects_count += 1
            
            logger.info(f"Module {module_name}: {mib_info.objects_count} objects, {mib_info.traps_count} traps")
    
    def _is_standard_mib(self, mib_name: str) -> bool:
        """Check if a MIB is a standard/system MIB"""
        standard_mibs = {
            'SNMPv2-SMI', 'SNMPv2-TC', 'SNMPv2-CONF', 'SNMPv2-MIB',
            'SNMP-FRAMEWORK-MIB', 'SNMP-MPD-MIB', 'SNMP-TARGET-MIB',
            'SNMP-NOTIFICATION-MIB', 'SNMP-PROXY-MIB', 'SNMP-USER-BASED-SM-MIB',
            'SNMP-VIEW-BASED-ACM-MIB', 'SNMP-COMMUNITY-MIB',
            'IANAifType-MIB', 'IANA-ADDRESS-FAMILY-NUMBERS-MIB',
            'INET-ADDRESS-MIB', 'IF-MIB', 'IP-MIB', 'TCP-MIB', 'UDP-MIB',
            'HOST-RESOURCES-MIB', 'ENTITY-MIB', 'BRIDGE-MIB',
            'RFC1155-SMI', 'RFC1213-MIB', 'RFC-1215'
        }
        
        return mib_name in standard_mibs
    
    def get_status(self) -> dict:
        """Get overall MIB service status"""
        return {
            "loaded": len(self.loaded_mibs),
            "failed": len(self.failed_mibs),
            "total": len(self.loaded_mibs) + len(self.failed_mibs),
            "mibs": [info.to_dict() for info in self.loaded_mibs.values()],
            "errors": [info.to_dict() for info in self.failed_mibs.values()]
        }
    
    def validate_mib_file(self, file_path: str) -> dict:
        """Validate a MIB file before loading"""
        result = {
            "valid": False,
            "mib_name": None,
            "imports": [],
            "missing_deps": [],
            "errors": []
        }
        
        try:
            mib_name = Path(file_path).stem
            result["mib_name"] = mib_name
            
            imports = self._extract_imports(file_path)
            result["imports"] = imports
            
            for imp in imports:
                if imp in self.loaded_mibs:
                    continue
                
                if self._is_standard_mib(imp):
                    continue
                
                if imp in self.mib_builder.mibSymbols:
                    continue
                
                result["missing_deps"].append(imp)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if 'DEFINITIONS' not in content:
                    result["errors"].append("Missing DEFINITIONS keyword")
                
                if 'BEGIN' not in content or 'END' not in content:
                    result["errors"].append("Missing BEGIN/END block")
            
            if not result["errors"]:
                result["valid"] = True
        
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
        
        return result
    
    def list_traps(self) -> List[dict]:
        """Enumerate all NOTIFICATION-TYPE objects"""
        traps = []
        seen_oids = set()  # Track OIDs to avoid duplicates
        
        for module_name, symbols in self.mib_builder.mibSymbols.items():
            module_trap_count = 0
            for symbol_name, symbol_obj in symbols.items():
                if symbol_obj.__class__.__name__ == 'NotificationType':
                    try:
                        oid_str = ".".join(map(str, symbol_obj.name))
                        
                        # Skip if we've already seen this OID
                        if oid_str in seen_oids:
                            logger.debug(f"Skipping duplicate trap: {module_name}::{symbol_name} ({oid_str})")
                            continue
                        
                        seen_oids.add(oid_str)
                        module_trap_count += 1
                        
                        trap_info = {
                            "module": module_name,
                            "name": symbol_name,
                            "full_name": f"{module_name}::{symbol_name}",
                            "oid": oid_str,
                            "description": symbol_obj.getDescription() or "No description",
                            "objects": []
                        }
                        
                        if hasattr(symbol_obj, 'getObjects'):
                            obj_list = symbol_obj.getObjects()
                            if obj_list:
                                for obj_name in obj_list:
                                    try:
                                        if isinstance(obj_name, tuple) and len(obj_name) >= 2:
                                            obj_module = obj_name[0]
                                            obj_symbol = obj_name[-1]
                                            
                                            if obj_module in self.mib_builder.mibSymbols:
                                                if obj_symbol in self.mib_builder.mibSymbols[obj_module]:
                                                    obj_def = self.mib_builder.mibSymbols[obj_module][obj_symbol]
                                                    
                                                    trap_info["objects"].append({
                                                        "name": obj_symbol,
                                                        "full_name": f"{obj_module}::{obj_symbol}",
                                                        "oid": ".".join(map(str, obj_def.name))
                                                    })
                                    except Exception as e:
                                        logger.debug(f"Error processing object {obj_name}: {e}")
                        
                        traps.append(trap_info)
                    
                    except Exception as e:
                        logger.debug(f"Error processing trap {symbol_name}: {e}")

            if module_trap_count > 0:
                logger.info(f"Module {module_name}: {module_trap_count} traps")
        
        logger.info(f"list_traps() returning {len(traps)} unique traps")
        return traps

    
    def list_objects(self, module_name: Optional[str] = None) -> List[dict]:
        """List all MIB objects"""
        objects = []
        
        modules = [module_name] if module_name else self.mib_builder.mibSymbols.keys()
        
        for mod in modules:
            if mod not in self.mib_builder.mibSymbols:
                continue
            
            symbols = self.mib_builder.mibSymbols[mod]
            
            for symbol_name, symbol_obj in symbols.items():
                class_name = symbol_obj.__class__.__name__
                
                if class_name in ['MibScalar', 'MibTableColumn']:
                    try:
                        objects.append({
                            "module": mod,
                            "name": symbol_name,
                            "full_name": f"{mod}::{symbol_name}",
                            "oid": ".".join(map(str, symbol_obj.name)),
                            "type": class_name,
                            "syntax": symbol_obj.getSyntax().__class__.__name__
                        })
                    except:
                        pass
        
        return objects
    
    def resolve_oid(self, oid: str, mode: str = "name") -> str:
        """Resolve OID to name or vice versa"""
        try:
            if mode == "numeric":
                # Name → Numeric
                if "::" not in oid:
                    # Already numeric
                    return oid
                
                parts = oid.split("::")
                if len(parts) != 2:
                    logger.warning(f"Invalid OID format: {oid}")
                    return oid
                
                module, name_with_index = parts
                
                # Check if MIB is loaded
                if module not in self.mib_builder.mibSymbols:
                    logger.error(f"MIB module '{module}' not loaded")
                    return oid
                
                # Handle index (e.g., "sysUpTime.0")
                if "." in name_with_index:
                    name, index = name_with_index.rsplit(".", 1)
                else:
                    name = name_with_index
                    index = None
                
                # Look up the symbol in the MIB
                if name not in self.mib_builder.mibSymbols[module]:
                    logger.error(f"Symbol '{name}' not found in module '{module}'")
                    return oid
                
                symbol_obj = self.mib_builder.mibSymbols[module][name]
                
                # Get the OID from the symbol
                if hasattr(symbol_obj, 'name'):
                    oid_tuple = symbol_obj.name
                    numeric = ".".join(map(str, oid_tuple))
                    
                    # Add index if present
                    if index:
                        numeric += "." + index
                    
                    logger.debug(f"Resolved {oid} -> {numeric}")
                    return numeric
                else:
                    logger.error(f"Symbol '{name}' has no OID")
                    return oid
            
            elif mode == "name":
                # Numeric → Name
                if "::" in oid:
                    # Already symbolic
                    return oid
                
                oid_tuple = tuple(int(x) for x in oid.strip('.').split('.'))
                
                try:
                    oid_obj, label, suffix = self.mib_view.getNodeName(oid_tuple)
                    
                    # Try to find MIB module name
                    for module_name, symbols in self.mib_builder.mibSymbols.items():
                        for symbol_name, symbol_obj in symbols.items():
                            if hasattr(symbol_obj, 'name') and symbol_obj.name == oid_obj:
                                result = f"{module_name}::{symbol_name}"
                                if suffix:
                                    result += "." + ".".join(map(str, suffix))
                                return result
                    
                    # Fallback
                    meaningful_labels = [l for l in label if l not in ['iso', 'org', 'dod', 'internet', 'mgmt', 'mib-2', 'private', 'enterprises']]
                    
                    if meaningful_labels:
                        result = "::".join(meaningful_labels[-2:]) if len(meaningful_labels) >= 2 else meaningful_labels[-1]
                    else:
                        result = "::".join(label[-2:]) if len(label) >= 2 else label[-1]
                    
                    if suffix:
                        result += "." + ".".join(map(str, suffix))
                    
                    return result
                except Exception as e:
                    logger.debug(f"Name resolution failed: {e}")
                    return oid
        
        except Exception as e:
            logger.error(f"OID resolution failed for '{oid}': {e}")
            return oid


    
    def get_trap_details(self, trap_identifier: str) -> Optional[dict]:
        """Get detailed information about a specific trap"""
        traps = self.list_traps()
        
        for trap in traps:
            if trap["full_name"] == trap_identifier or trap["oid"] == trap_identifier:
                return trap
        
        return None
    
    def _build_tree_structure(self):
        """Build hierarchical tree from loaded MIBs"""
        logger.info("Building OID tree structure...")
        
        # Clear existing structures
        self.oid_tree.clear()
        self.oid_index.clear()
        self.name_index.clear()
        self.search_index.clear()
        self.module_roots.clear()
        
        # Extract all nodes
        for module_name, symbols in self.mib_builder.mibSymbols.items():
            if module_name not in self.module_roots:
                self.module_roots[module_name] = []
            
            for symbol_name, symbol_obj in symbols.items():
                if not hasattr(symbol_obj, 'name'):
                    continue
                
                try:
                    oid_tuple = tuple(symbol_obj.name)
                    
                    # Create node
                    node = OidNode(
                        oid=oid_tuple,
                        name=symbol_name,
                        module=module_name,
                        node_type=symbol_obj.__class__.__name__
                    )
                    
                    # Extract metadata
                    if hasattr(symbol_obj, 'getSyntax'):
                        try:
                            syntax_obj = symbol_obj.getSyntax()
                            node.syntax = syntax_obj.__class__.__name__
                        except:
                            pass
                    
                    if hasattr(symbol_obj, 'getMaxAccess'):
                        try:
                            node.access = symbol_obj.getMaxAccess()
                        except:
                            pass
                    
                    if hasattr(symbol_obj, 'getStatus'):
                        try:
                            node.status = symbol_obj.getStatus()
                        except:
                            pass
                    
                    if hasattr(symbol_obj, 'getDescription'):
                        try:
                            desc = symbol_obj.getDescription()
                            node.description = desc if desc else ""
                        except:
                            pass
                    
                    # Extract indexes for tables
                    if hasattr(symbol_obj, 'getIndexNames'):
                        try:
                            indexes = symbol_obj.getIndexNames()
                            node.indexes = [str(idx) for idx in indexes]
                        except:
                            pass
                    
                    # Store node
                    self.oid_tree[oid_tuple] = node
                    self.name_index[node.full_name] = oid_tuple
                    self.oid_index[node.oid_str] = oid_tuple
                    
                    # Track module roots (top-level objects in each module)
                    if len(oid_tuple) <= 10:  # Heuristic for "root" objects
                        self.module_roots[module_name].append(oid_tuple)
                
                except Exception as e:
                    logger.debug(f"Failed to process symbol {symbol_name}: {e}")
        
        # Build parent-child relationships
        for oid_tuple, node in self.oid_tree.items():
            if len(oid_tuple) > 1:
                parent_oid = oid_tuple[:-1]
                if parent_oid in self.oid_tree:
                    node.parent_oid = parent_oid
                    if oid_tuple not in self.oid_tree[parent_oid].children:
                        self.oid_tree[parent_oid].children.append(oid_tuple)
        
        # Sort children by OID
        for node in self.oid_tree.values():
            node.children.sort()
        
        # Build search index
        self._build_search_index()
        
        logger.info(f"Tree built: {len(self.oid_tree)} nodes, {len(self.module_roots)} modules")
    
    def _build_search_index(self):
        """Build keyword search index"""
        self.search_index.clear()
        
        for oid_tuple, node in self.oid_tree.items():
            keywords = set()
            
            # Index by name (case-insensitive)
            keywords.add(node.name.lower())
            
            # Index by module
            keywords.add(node.module.lower())
            
            # Index by name parts (split camelCase and snake_case)
            name_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', node.name)
            keywords.update(part.lower() for part in name_parts if len(part) > 2)
            
            # Index description words (only significant words)
            if node.description:
                words = re.findall(r'\b[a-zA-Z]{4,}\b', node.description.lower())
                keywords.update(words[:20])  # Limit to first 20 words
            
            # Store in index
            for keyword in keywords:
                if keyword not in self.search_index:
                    self.search_index[keyword] = set()
                self.search_index[keyword].add(oid_tuple)
    
    def get_module_tree(self, module_name: Optional[str] = None) -> List[dict]:
        """Get tree organized by modules"""
        if module_name:
            modules = [module_name] if module_name in self.loaded_mibs or module_name in self.mib_builder.mibSymbols else []
        else:
            # Include both loaded MIBs and system MIBs
            all_modules = set(self.loaded_mibs.keys())
            all_modules.update(self.mib_builder.mibSymbols.keys())
            modules = sorted(all_modules)
        
        result = []
        for mod in modules:
            # Check if it's a loaded MIB or system MIB
            is_system_mib = mod not in self.loaded_mibs and mod in self.mib_builder.mibSymbols
            
            module_node = {
                "oid": f"module:{mod}",
                "name": mod,
                "full_name": mod,
                "module": mod,
                "type": "Module",
                "has_children": True,
                "children": [],
                "is_system": is_system_mib  # NEW flag
            }
            
            # Get ALL objects for this module
            module_objects = []
            if mod in self.mib_builder.mibSymbols:
                for symbol_name, symbol_obj in self.mib_builder.mibSymbols[mod].items():
                    if hasattr(symbol_obj, 'name'):
                        try:
                            oid_tuple = tuple(symbol_obj.name)
                            if oid_tuple in self.oid_tree:
                                module_objects.append(self.oid_tree[oid_tuple])
                        except:
                            pass
            
            # Sort by OID
            module_objects.sort(key=lambda n: n.oid)
            
            # Convert to dict
            for node in module_objects:
                module_node["children"].append(node.to_dict())
            
            if len(module_node["children"]) > 0:  # Only include modules with objects
                result.append(module_node)
        
        return result
    
    def get_oid_tree(self, root_oid: str, depth: int = 1, module_filter: Optional[str] = None) -> dict:
        """Get OID tree starting from root_oid"""
        try:
            oid_tuple = tuple(int(x) for x in root_oid.strip('.').split('.'))
        except:
            raise ValueError("Invalid OID format")
        
        # Get or create root node
        if oid_tuple in self.oid_tree:
            root_node = self.oid_tree[oid_tuple].to_dict()
        else:
            # Create virtual node for standard OIDs
            root_node = {
                "oid": root_oid,
                "name": self._get_standard_oid_name(oid_tuple),
                "full_name": root_oid,
                "module": "Standard",
                "type": "node",
                "has_children": True
            }
        
        # Get children recursively
        children = self._get_tree_children(oid_tuple, depth, module_filter)
        
        return {
            "root": root_node,
            "children": children,
            "total_descendants": len(children)
        }
    
    def _get_tree_children(self, parent_oid: tuple, depth: int, module_filter: Optional[str]) -> List[dict]:
        """Recursively get children up to specified depth"""
        if depth <= 0:
            return []
        
        children = []
        
        if parent_oid in self.oid_tree:
            parent_node = self.oid_tree[parent_oid]
            
            for child_oid in parent_node.children:
                if child_oid not in self.oid_tree:
                    continue
                
                child_node = self.oid_tree[child_oid]
                
                # Apply module filter
                if module_filter and child_node.module != module_filter:
                    continue
                
                child_dict = child_node.to_dict()
                
                # Recursively get grandchildren if depth > 1
                if depth > 1 and child_node.children:
                    child_dict["children"] = self._get_tree_children(child_oid, depth - 1, module_filter)
                
                children.append(child_dict)
        else:
            # For virtual nodes, find all nodes that start with this OID
            for oid_tuple, node in self.oid_tree.items():
                if len(oid_tuple) == len(parent_oid) + 1 and oid_tuple[:len(parent_oid)] == parent_oid:
                    if module_filter and node.module != module_filter:
                        continue
                    children.append(node.to_dict())
        
        return children
    
    def _get_standard_oid_name(self, oid_tuple: tuple) -> str:
        """Get human-readable name for standard OIDs"""
        standard_names = {
            (1,): "iso",
            (1, 3): "org",
            (1, 3, 6): "dod",
            (1, 3, 6, 1): "internet",
            (1, 3, 6, 1, 1): "directory",
            (1, 3, 6, 1, 2): "mgmt",
            (1, 3, 6, 1, 2, 1): "mib-2",
            (1, 3, 6, 1, 3): "experimental",
            (1, 3, 6, 1, 4): "private",
            (1, 3, 6, 1, 4, 1): "enterprises"
        }
        return standard_names.get(oid_tuple, f"OID-{'.'.join(map(str, oid_tuple))}")
    
    def get_node_details(self, oid_identifier: str) -> dict:
        """Get detailed information about a specific OID node"""
        # Try numeric OID first
        if oid_identifier in self.oid_index:
            oid_tuple = self.oid_index[oid_identifier]
        # Try symbolic name
        elif oid_identifier in self.name_index:
            oid_tuple = self.name_index[oid_identifier]
        else:
            raise ValueError("OID not found")
        
        node = self.oid_tree[oid_tuple]
        
        # Get siblings
        siblings = []
        if node.parent_oid and node.parent_oid in self.oid_tree:
            parent = self.oid_tree[node.parent_oid]
            siblings = [
                self.oid_tree[child_oid].to_dict()
                for child_oid in parent.children
                if child_oid != oid_tuple
            ]
        
        # Get breadcrumb
        breadcrumb = self._get_breadcrumb(oid_tuple)
        
        return {
            "node": node.to_dict(),
            "siblings": siblings,
            "breadcrumb": breadcrumb
        }
    
    def _get_breadcrumb(self, oid_tuple: tuple) -> List[dict]:
        """Get simplified path showing only MIB hierarchy"""
        breadcrumb = []
        current = oid_tuple
        visited = set()
        
        # Collect all nodes in path
        path_nodes = []
        while current and current not in visited:
            visited.add(current)
            
            if current in self.oid_tree:
                node = self.oid_tree[current]
                path_nodes.insert(0, node)
                current = node.parent_oid
            else:
                if len(current) > 1:
                    current = current[:-1]
                else:
                    break
        
        # Build breadcrumb from path nodes
        # Group by module and show hierarchy within module
        if path_nodes:
            current_module = None
            
            for node in path_nodes:
                # Skip if same module already shown (avoid repetition)
                if node.module != current_module:
                    current_module = node.module
                
                # Only show meaningful nodes (skip internal identifiers)
                if node.name not in ['PYSNMP_MODULE_ID', 'pysnmp', 'iso', 'org', 'dod', 'internet']:
                    breadcrumb.append({
                        "oid": node.oid_str,
                        "name": node.name,
                        "full_name": node.full_name,
                        "module": node.module
                    })
        
        return breadcrumb
    
    def search_oids(self, query: str, limit: int = 100, module_filter: Optional[str] = None, 
                    type_filter: Optional[str] = None) -> dict:
        """Search OIDs by name, description, or OID"""
        query_lower = query.lower()
        matching_oids = set()
        
        # Exact name match
        if query in self.name_index:
            matching_oids.add(self.name_index[query])
        
        # Keyword search in index
        for keyword, oid_set in self.search_index.items():
            if query_lower in keyword:
                matching_oids.update(oid_set)
        
        # Numeric OID search
        if re.match(r'^[\d.]+$', query):
            for oid_str, oid_tuple in self.oid_index.items():
                if query in oid_str:
                    matching_oids.add(oid_tuple)
        
        # Filter and format results
        results = []
        for oid_tuple in matching_oids:
            if oid_tuple not in self.oid_tree:
                continue
            
            node = self.oid_tree[oid_tuple]
            
            # Apply filters
            if module_filter and node.module != module_filter:
                continue
            if type_filter and node.node_type != type_filter:
                continue
            
            results.append(node.to_dict())
            
            if len(results) >= limit:
                break
        
        # Sort by relevance (exact matches first, then by name)
        results.sort(key=lambda x: (
            0 if query_lower == x["name"].lower() else 1,
            x["name"].lower()
        ))
        
        return {
            "query": query,
            "count": len(results),
            "results": results
        }
    
    def get_module_stats(self) -> List[dict]:
        """Get statistics for all modules"""
        modules = {}
        
        for oid_tuple, node in self.oid_tree.items():
            if node.module not in modules:
                modules[node.module] = {
                    "name": node.module,
                    "objects": 0,
                    "scalars": 0,
                    "tables": 0,
                    "columns": 0,
                    "notifications": 0
                }
            
            modules[node.module]["objects"] += 1
            
            if "Scalar" in node.node_type:
                modules[node.module]["scalars"] += 1
            elif "Table" in node.node_type and "Column" not in node.node_type:
                modules[node.module]["tables"] += 1
            elif "Column" in node.node_type:
                modules[node.module]["columns"] += 1
            elif "Notification" in node.node_type:
                modules[node.module]["notifications"] += 1
        
        return sorted(modules.values(), key=lambda x: x["name"])
    
    def reload(self):
        """Hot-reload all MIBs"""
        logger.info("Reloading MIB service...")
        
        # Clear ALL data structures
        self.mib_builder = builder.MibBuilder()
        self.mib_view = view.MibViewController(self.mib_builder)
        self.loaded_mibs.clear()
        self.failed_mibs.clear()
        self.oid_tree.clear()
        self.oid_index.clear()
        self.name_index.clear()
        self.search_index.clear()
        self.module_roots.clear()
        
        # Force garbage collection to clear old references
        import gc
        gc.collect()
        
        # Reconfigure and reload
        self._configure_sources()
        self._load_all_mibs()
        self._build_tree_structure()
        
        logger.info(f"Reload complete: {len(self.loaded_mibs)} loaded, {len(self.oid_tree)} nodes indexed")
        
        # Log trap counts for debugging
        total_traps = sum(mib.traps_count for mib in self.loaded_mibs.values())
        logger.info(f"Total traps across all MIBs: {total_traps}")

_mib_service_instance = None

def get_mib_service() -> MibService:
    """Get or create the MibService singleton"""
    global _mib_service_instance
    if _mib_service_instance is None:
        _mib_service_instance = MibService()
    return _mib_service_instance
