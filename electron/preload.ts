import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  selectFile: () => ipcRenderer.invoke('dialog:openFile'),
});