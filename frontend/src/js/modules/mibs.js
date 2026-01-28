window.MibsModule = {
    currentTrapData: null,
    uploadModal: null,
    trapDetailsModal: null,
    allTraps: [],

    init: function() {
        this.uploadModal = new bootstrap.Modal(document.getElementById('uploadModal'));
        this.trapDetailsModal = new bootstrap.Modal(document.getElementById('trapDetailsModal'));

        this.loadStatus();
        this.loadTraps();

        document.getElementById('trap-search').addEventListener('input', (e) => {
            this.filterTraps(e.target.value);
        });
    },

    loadStatus: async function() {
        try {
            const res = await fetch('/api/mibs/status');
            const data = await res.json();

            document.getElementById('mib-count-loaded').textContent = data.loaded;
            document.getElementById('mib-count-failed').textContent = data.failed;

            const totalTraps = data.mibs.reduce((sum, mib) => sum + mib.traps, 0);
            document.getElementById('mib-count-traps').textContent = totalTraps;

            this.renderMibList(data.mibs);

            if (data.errors.length > 0) {
                this.renderFailedMibs(data.errors);
            }
        } catch (e) {
            console.error('Failed to load MIB status', e);
        }
    },

    renderMibList: function(mibs) {
        const list = document.getElementById('mib-list');
        
        if (mibs.length === 0) {
            list.innerHTML = '<li class="list-group-item text-center text-muted">No MIBs loaded</li>';
            return;
        }

        list.innerHTML = mibs.map(mib => `
            <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-book text-primary me-2"></i>
                        <strong>${mib.name}</strong>
                        <span class="badge bg-success ms-2">✓</span>
                    </div>
                    <small class="text-muted d-block mt-1">
                        ${mib.objects} objects · ${mib.traps} traps
                        ${mib.imports.length > 0 ? `· Imports: ${mib.imports.slice(0, 3).join(', ')}${mib.imports.length > 3 ? '...' : ''}` : ''}
                    </small>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="MibsModule.deleteMib('${mib.file}')">
                    <i class="fas fa-trash"></i>
                </button>
            </li>
        `).join('');
    },

    renderFailedMibs: function(errors) {
        const card = document.getElementById('failed-mibs-card');
        const list = document.getElementById('failed-mib-list');

        card.style.display = 'block';

        list.innerHTML = errors.map(mib => `
            <li class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong class="text-danger">${mib.name}</strong>
                        <div class="small text-muted mt-1">${mib.error || 'Unknown error'}</div>
                        ${mib.status === 'missing_deps' ? `
                            <div class="badge bg-warning text-dark mt-1">Missing dependencies</div>
                        ` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="MibsModule.deleteMib('${mib.file}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </li>
        `).join('');
    },

    loadTraps: async function() {
        try {
            const res = await fetch('/api/mibs/traps');
            const data = await res.json();

            this.allTraps = data.traps;
            this.renderTraps(data.traps);
        } catch (e) {
            console.error('Failed to load traps', e);
        }
    },

    renderTraps: function(traps) {
        const tbody = document.getElementById('trap-table-body');

        if (traps.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted p-3">No traps found</td></tr>';
            return;
        }

        tbody.innerHTML = traps.map(trap => `
            <tr>
                <td>
                    <strong>${trap.name}</strong>
                    <div class="small text-muted">${trap.description.substring(0, 50)}${trap.description.length > 50 ? '...' : ''}</div>
                </td>
                <td><code class="small">${trap.oid}</code></td>
                <td><span class="badge bg-secondary">${trap.module}</span></td>
                <td class="text-center">
                    <span class="badge bg-info">${trap.objects.length}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick='MibsModule.showTrapDetails(${JSON.stringify(trap).replace(/'/g, "&apos;")})'>
                        <i class="fas fa-info-circle"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    },

    filterTraps: function(query) {
        if (!this.allTraps) return;

        const filtered = this.allTraps.filter(trap => {
            const searchStr = `${trap.name} ${trap.module} ${trap.oid} ${trap.description}`.toLowerCase();
            return searchStr.includes(query.toLowerCase());
        });

        this.renderTraps(filtered);
    },

    showTrapDetails: function(trap) {
        this.currentTrapData = trap;

        const title = document.getElementById('trap-detail-title');
        const body = document.getElementById('trap-detail-body');

        title.textContent = trap.full_name;

        body.innerHTML = `
            <div class="mb-3">
                <label class="fw-bold">OID:</label>
                <div><code>${trap.oid}</code></div>
            </div>
            <div class="mb-3">
                <label class="fw-bold">Module:</label>
                <div><span class="badge bg-secondary">${trap.module}</span></div>
            </div>
            <div class="mb-3">
                <label class="fw-bold">Description:</label>
                <div class="text-muted">${trap.description}</div>
            </div>
            <div class="mb-3">
                <label class="fw-bold">Associated Objects (VarBinds):</label>
                ${trap.objects.length > 0 ? `
                    <ul class="list-group mt-2">
                        ${trap.objects.map(obj => `
                            <li class="list-group-item d-flex justify-content-between">
                                <span><code>${obj.name}</code></span>
                                <span class="text-muted small">${obj.oid}</span>
                            </li>
                        `).join('')}
                    </ul>
                ` : '<div class="text-muted">No associated objects defined</div>'}
            </div>
        `;

        this.trapDetailsModal.show();
    },

    useTrapInSender: function() {
        if (!this.currentTrapData) return;

        sessionStorage.setItem('selectedTrap', JSON.stringify(this.currentTrapData));
        window.location.hash = '#traps';
        this.trapDetailsModal.hide();
    },

    showUploadModal: function() {
        document.getElementById('mib-upload-input').value = '';
        document.getElementById('upload-validation-results').style.display = 'none';
        document.getElementById('dependency-alert').style.display = 'none';
        document.getElementById('btn-validate').disabled = false;
        document.getElementById('btn-upload').disabled = true;

        this.uploadModal.show();
    },

    validateFiles: async function() {
        const input = document.getElementById('mib-upload-input');
        if (!input.files || input.files.length === 0) {
            alert('Please select at least one file');
            return;
        }

        const btn = document.getElementById('btn-validate');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validating...';
        btn.disabled = true;

        const resultsDiv = document.getElementById('upload-validation-results');
        const validationList = document.getElementById('validation-list');
        const depAlert = document.getElementById('dependency-alert');
        const depList = document.getElementById('dependency-list');

        try {
            const formData = new FormData();
            for (let file of input.files) {
                formData.append('files', file);
            }

            const res = await fetch('/api/mibs/validate-batch', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            validationList.innerHTML = data.files.map(r => {
                const hasLocalMissing = r.missing_deps.length > 0;
                const statusClass = r.valid ? 'border-success' : 'border-danger';
                const statusBadge = r.valid ? 
                    '<span class="badge bg-success">✓ Valid</span>' : 
                    '<span class="badge bg-danger">✗ Invalid</span>';

                return `
                    <div class="card mb-2 ${statusClass}">
                        <div class="card-body p-2">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${r.filename}</strong>
                                    <span class="text-muted small ms-2">(${r.mib_name})</span>
                                </div>
                                ${statusBadge}
                            </div>
                            
                            ${r.errors.length > 0 ? `
                                <div class="alert alert-danger py-1 px-2 mt-2 mb-0 small">
                                    <strong>Errors:</strong><br>
                                    ${r.errors.join('<br>')}
                                </div>
                            ` : ''}
                            
                            ${r.imports.length > 0 ? `
                                <div class="text-muted small mt-2">
                                    <strong>Imports:</strong> ${r.imports.join(', ')}
                                </div>
                            ` : ''}
                            
                            ${hasLocalMissing ? `
                                <div class="alert alert-warning py-1 px-2 mt-2 mb-0 small">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    <strong>Missing:</strong> ${r.missing_deps.join(', ')}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');

            resultsDiv.style.display = 'block';

            if (data.global_missing_deps.length > 0) {
                depList.innerHTML = `
                    <p class="mb-2">The following dependencies are not available:</p>
                    <ul class="mb-2">
                        ${data.global_missing_deps.map(dep => `
                            <li><code>${dep}</code></li>
                        `).join('')}
                    </ul>
                    <p class="mb-0 small">
                        <strong>Options:</strong><br>
                        • Upload these MIBs in a separate batch first<br>
                        • Continue anyway (affected MIBs will fail to load)
                    </p>
                `;
                depAlert.style.display = 'block';
            } else {
                depAlert.style.display = 'none';
            }

            document.getElementById('btn-upload').disabled = !data.can_upload;

            if (data.can_upload) {
                document.getElementById('btn-upload').innerHTML = 
                    '<i class="fas fa-upload"></i> Upload & Reload';
            } else {
                document.getElementById('btn-upload').innerHTML = 
                    '<i class="fas fa-ban"></i> Cannot Upload (Fix Errors)';
            }

        } catch (e) {
            console.error('Validation error:', e);
            alert('Validation failed: ' + e.message);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },

    uploadFiles: async function() {
        const input = document.getElementById('mib-upload-input');
        const btn = document.getElementById('btn-upload');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        btn.disabled = true;

        try {
            const formData = new FormData();
            for (let file of input.files) {
                formData.append('files', file);
            }

            const res = await fetch('/api/mibs/upload', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Upload failed (${res.status}): ${errorText}`);
            }

            const data = await res.json();

            if (!data || !data.results || !Array.isArray(data.results)) {
                throw new Error('Invalid response format from server');
            }

            const loaded = data.results.filter(r => r.status === 'loaded').length;
            const failed = data.results.filter(r => r.status === 'failed').length;
            const errors = data.results.filter(r => r.status === 'error').length;

            let message = `Upload Complete!\n\n`;
            message += `✓ Successfully loaded: ${loaded}\n`;
            
            if (failed > 0) {
                message += `⚠ Failed to load: ${failed}\n`;
            }
            
            if (errors > 0) {
                message += `✗ Upload errors: ${errors}\n`;
            }

            const problemFiles = data.results.filter(r => 
                r.status === 'failed' || r.status === 'error'
            );
            
            if (problemFiles.length > 0) {
                message += `\nDetails:\n`;
                problemFiles.forEach(r => {
                    message += `• ${r.filename}: ${r.error || 'Unknown error'}\n`;
                });
            }

            alert(message);

            await this.loadStatus();
            await this.loadTraps();

            this.uploadModal.hide();

        } catch (e) {
            console.error('Upload error:', e);
            alert('Upload failed:\n\n' + e.message);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },

    reloadMibs: async function() {
        try {
            const res = await fetch('/api/mibs/reload', { method: 'POST' });
            const data = await res.json();

            await this.loadStatus();
            await this.loadTraps();

            console.log('MIBs reloaded:', data);
        } catch (e) {
            console.error('Reload failed', e);
        }
    },

    deleteMib: async function(filename) {
        if (!confirm(`Delete ${filename}?`)) return;

        try {
            await fetch(`/api/mibs/${filename}`, { method: 'DELETE' });
            await this.reloadMibs();
        } catch (e) {
            alert('Delete failed: ' + e.message);
        }
    },

    showDependencyHelp: function() {
        alert(
            'How to resolve missing dependencies:\n\n' +
            '1. Download the required MIB files from vendor websites or mibs.pysnmp.com\n' +
            '2. Upload them using this same dialog\n' +
            '3. Re-upload the original MIB after dependencies are loaded\n\n' +
            'Common sources:\n' +
            '- Standard MIBs: https://www.iana.org/assignments/ianaiftype-mib\n' +
            '- Vendor MIBs: Check manufacturer support pages'
        );
    }
};
