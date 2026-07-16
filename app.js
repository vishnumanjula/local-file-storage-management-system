// File Storage Application
// Manages two storage locations with comprehensive logging

class FileStorage {
    constructor() {
        this.allFiles = [];
        this.penDriveFiles = [];
        this.logs = [];
        this.selectMode = { all: false, pen: false };
        this.selectedFiles = { all: new Set(), pen: new Set() };
        
        this.init();
    }

    init() {
        this.loadFromStorage();
        this.setupEventListeners();
        this.render();
        this.addLog('system', 'System initialized', 'File storage system started');
    }

    setupEventListeners() {
        // Upload handlers
        document.getElementById('uploadAllFiles').addEventListener('change', (e) => {
            this.handleUpload(e.target.files, 'all');
        });
        
        document.getElementById('uploadPenDrive').addEventListener('change', (e) => {
            this.handleUpload(e.target.files, 'pen');
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.exitSelectMode();
                closeModal();
            }
        });
    }

    handleUpload(files, location) {
        Array.from(files).forEach(file => {
            const fileData = {
                id: Date.now() + Math.random().toString(36).substr(2, 9),
                name: file.name,
                size: file.size,
                type: file.type,
                lastModified: file.lastModified,
                content: null,
                uploadedAt: new Date().toISOString()
            };

            // Read file content
            const reader = new FileReader();
            reader.onload = (e) => {
                fileData.content = e.target.result;
                
                if (location === 'all') {
                    this.allFiles.push(fileData);
                } else {
                    this.penDriveFiles.push(fileData);
                }
                
                this.addLog('add', `File uploaded to ${location === 'all' ? 'All Files' : 'Pen Drive'}`, file.name);
                this.saveToStorage();
                this.render();
            };
            
            if (file.type.startsWith('image/') || file.type.startsWith('text/')) {
                reader.readAsDataURL(file);
            } else {
                reader.readAsArrayBuffer(file);
            }
        });
    }

    deleteFile(id, location) {
        const files = location === 'all' ? this.allFiles : this.penDriveFiles;
        const file = files.find(f => f.id === id);
        
        if (file) {
            if (location === 'all') {
                this.allFiles = this.allFiles.filter(f => f.id !== id);
            } else {
                this.penDriveFiles = this.penDriveFiles.filter(f => f.id !== id);
            }
            
            this.selectedFiles[location].delete(id);
            this.addLog('delete', `File deleted from ${location === 'all' ? 'All Files' : 'Pen Drive'}`, file.name);
            this.saveToStorage();
            this.render();
        }
    }

    copyFile(id, from, to) {
        const sourceFiles = from === 'all' ? this.allFiles : this.penDriveFiles;
        const file = sourceFiles.find(f => f.id === id);
        
        if (file) {
            const newFile = {
                ...file,
                id: Date.now() + Math.random().toString(36).substr(2, 9),
                copiedAt: new Date().toISOString()
            };
            
            if (to === 'all') {
                this.allFiles.push(newFile);
            } else {
                this.penDriveFiles.push(newFile);
            }
            
            this.addLog('copy', `File copied from ${from === 'all' ? 'All Files' : 'Pen Drive'} to ${to === 'all' ? 'All Files' : 'Pen Drive'}`, file.name);
            this.saveToStorage();
            this.render();
        }
    }

    copySelected(targetLocation) {
        const source = targetLocation === 'all' ? 'pen' : 'all';
        const selectedIds = Array.from(this.selectedFiles[source]);
        
        selectedIds.forEach(id => {
            this.copyFile(id, source, targetLocation);
        });
        
        this.exitSelectMode();
    }

    toggleFileSelection(id, location) {
        if (this.selectedFiles[location].has(id)) {
            this.selectedFiles[location].delete(id);
        } else {
            this.selectedFiles[location].add(id);
        }
        this.render();
        this.updateTransferButtons();
    }

    updateTransferButtons() {
        const allSelected = this.selectedFiles.all.size > 0;
        const penSelected = this.selectedFiles.pen.size > 0;
        
        document.getElementById('copyToPenDrive').disabled = !allSelected;
        document.getElementById('copyToAllFiles').disabled = !penSelected;
    }

    viewFile(id, location) {
        const files = location === 'all' ? this.allFiles : this.penDriveFiles;
        const file = files.find(f => f.id === id);
        
        if (file) {
            document.getElementById('previewTitle').textContent = file.name;
            const content = document.getElementById('previewContent');
            
            if (file.type.startsWith('image/')) {
                content.innerHTML = `<img src="${file.content}" alt="${file.name}">`;
            } else if (file.type === 'application/pdf') {
                content.innerHTML = `<iframe src="${file.content}" title="${file.name}"></iframe>`;
            } else if (file.type.startsWith('text/')) {
                content.innerHTML = `<pre style="text-align: left; background: #f5f5f5; padding: 20px; border-radius: 8px; overflow-x: auto;">${file.content}</pre>`;
            } else {
                content.innerHTML = `<p>Preview not available for this file type.<br>File: ${file.name}<br>Size: ${this.formatSize(file.size)}</p>`;
            }
            
            document.getElementById('previewModal').style.display = 'block';
            this.addLog('view', `File viewed in ${location === 'all' ? 'All Files' : 'Pen Drive'}`, file.name);
        }
    }

    downloadFile(id, location) {
        const files = location === 'all' ? this.allFiles : this.penDriveFiles;
        const file = files.find(f => f.id === id);
        
        if (file && file.content) {
            const link = document.createElement('a');
            link.href = file.content;
            link.download = file.name;
            link.click();
            this.addLog('download', `File downloaded from ${location === 'all' ? 'All Files' : 'Pen Drive'}`, file.name);
        }
    }

    addLog(action, details, filename = '') {
        const log = {
            id: Date.now() + Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toISOString(),
            action: action,
            details: details,
            filename: filename
        };
        
        this.logs.unshift(log);
        this.saveToStorage();
        this.renderLogs();
    }

    renderLogs() {
        const container = document.getElementById('logsContainer');
        
        if (this.logs.length === 0) {
            container.innerHTML = '<p class="empty-msg" style="color: #90a4ae;">No activity recorded yet.</p>';
            return;
        }
        
        container.innerHTML = this.logs.map(log => {
            const time = new Date(log.timestamp).toLocaleTimeString();
            return `
                <div class="log-entry">
                    <span class="log-time">${time}</span>
                    <span class="log-action ${log.action}">${log.action.toUpperCase()}</span>
                    <span class="log-details">${log.details}${log.filename ? ': ' + log.filename : ''}</span>
                </div>
            `;
        }).join('');
    }

    render() {
        this.renderFileList('allFilesList', this.allFiles, 'all');
        this.renderFileList('penDriveList', this.penDriveFiles, 'pen');
        document.getElementById('allFilesCount').textContent = `${this.allFiles.length} files`;
        document.getElementById('penDriveCount').textContent = `${this.penDriveFiles.length} files`;
        this.updateTransferButtons();
    }

    renderFileList(containerId, files, location) {
        const container = document.getElementById(containerId);
        
        if (files.length === 0) {
            container.innerHTML = '<p class="empty-msg">No files yet. Upload files here.</p>';
            return;
        }
        
        container.innerHTML = files.map(file => {
            const isSelected = this.selectedFiles[location].has(file.id);
            const iconClass = this.getFileIconClass(file.type);
            const icon = this.getFileIcon(file.type);
            
            return `
                <div class="file-item ${isSelected ? 'selected' : ''}" onclick="${this.selectMode[location] ? `storage.toggleFileSelection('${file.id}', '${location}')` : `storage.viewFile('${file.id}', '${location}')`}">
                    ${this.selectMode[location] ? `<input type="checkbox" class="file-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); storage.toggleFileSelection('${file.id}', '${location}')">` : ''}
                    <div class="file-icon ${iconClass}">${icon}</div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${this.formatSize(file.size)}</div>
                    </div>
                    <div class="file-actions" onclick="event.stopPropagation()">
                        <button class="btn-view" onclick="storage.viewFile('${file.id}', '${location}')" title="View">👁</button>
                        <button class="btn-download" onclick="storage.downloadFile('${file.id}', '${location}')" title="Download">⬇</button>
                        <button class="btn-delete" onclick="storage.deleteFile('${file.id}', '${location}')" title="Delete">🗑</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    getFileIconClass(type) {
        if (type.startsWith('image/')) return 'image';
        if (type === 'application/pdf') return 'pdf';
        if (type.startsWith('text/') || type.includes('document')) return 'document';
        if (type.startsWith('video/')) return 'video';
        if (type.startsWith('audio/')) return 'audio';
        return 'other';
    }

    getFileIcon(type) {
        if (type.startsWith('image/')) return '🖼';
        if (type === 'application/pdf') return '📄';
        if (type.startsWith('text/') || type.includes('document')) return '📝';
        if (type.startsWith('video/')) return '🎬';
        if (type.startsWith('audio/')) return '🎵';
        return '📦';
    }

    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    exitSelectMode() {
        this.selectMode = { all: false, pen: false };
        this.selectedFiles = { all: new Set(), pen: new Set() };
        document.getElementById('selectAllBtn').classList.remove('active');
        document.getElementById('selectPenBtn').classList.remove('active');
        this.render();
    }

    saveToStorage() {
        // Save to localStorage
        const data = {
            allFiles: this.allFiles.map(f => ({ ...f, content: null })), // Don't save binary content
            penDriveFiles: this.penDriveFiles.map(f => ({ ...f, content: null })),
            logs: this.logs
        };
        localStorage.setItem('fileStorage_metadata', JSON.stringify(data));
    }

    loadFromStorage() {
        const saved = localStorage.getItem('fileStorage_metadata');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.allFiles = data.allFiles || [];
                this.penDriveFiles = data.penDriveFiles || [];
                this.logs = data.logs || [];
            } catch (e) {
                console.error('Failed to load storage:', e);
            }
        }
    }
}

// Global functions for UI interactions
function toggleSelectMode(location) {
    storage.selectMode[location] = !storage.selectMode[location];
    
    const btnId = location === 'all' ? 'selectAllBtn' : 'selectPenBtn';
    const btn = document.getElementById(btnId);
    
    if (storage.selectMode[location]) {
        btn.classList.add('active');
        btn.textContent = 'Done';
    } else {
        btn.classList.remove('active');
        btn.textContent = 'Select Files';
        storage.selectedFiles[location].clear();
    }
    
    storage.render();
    storage.updateTransferButtons();
}

function copySelectedToPenDrive() {
    storage.copySelected('pen');
}

function copySelectedToAllFiles() {
    storage.copySelected('all');
}

function clearLogs() {
    if (confirm('Are you sure you want to clear all logs?')) {
        storage.logs = [];
        storage.saveToStorage();
        storage.renderLogs();
        storage.addLog('system', 'Logs cleared', '');
    }
}

function downloadLogs() {
    const logText = storage.logs.map(log => {
        const time = new Date(log.timestamp).toLocaleString();
        return `[${time}] [${log.action.toUpperCase()}] ${log.details}${log.filename ? ': ' + log.filename : ''}`;
    }).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `file-storage-logs-${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
}

function closeModal() {
    document.getElementById('previewModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('previewModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Initialize storage
const storage = new FileStorage();
