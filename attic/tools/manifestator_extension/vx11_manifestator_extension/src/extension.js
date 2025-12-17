const vscode = require('vscode');
const fetch = require('node-fetch');

function activate(context) {
    let disposable = vscode.commands.registerCommand('vx11.manifestator.drift', async function () {
        const config = vscode.workspace.getConfiguration('vx11Manifestator');
        const apiUrl = config.get('apiUrl') || 'http://127.0.0.1:52115';
        const token = config.get('token') || 'vx11-dev-token-change-in-production';

        try {
            const res = await fetch(`${apiUrl}/drift`, {
                method: 'GET',
                headers: { 'X-VX11-Token': token }
            });
            const data = await res.json();
            vscode.window.showInformationMessage('Manifestator drift completed. See output.');
            const out = vscode.window.createOutputChannel('VX11 Manifestator');
            out.appendLine(JSON.stringify(data, null, 2));
            out.show(true);
        } catch (e) {
            vscode.window.showErrorMessage('Failed to call manifestator drift: ' + e.message);
        }
    });

    context.subscriptions.push(disposable);
}

function deactivate() { }

module.exports = { activate, deactivate };
