const { execSync } = require("child_process");
const { shell, dialog } = require("electron");

function checkFullDiskAccess() {
  try {
    const mailDb = require("path").join(
      require("os").homedir(),
      "Library/Mail"
    );
    require("fs").accessSync(mailDb, require("fs").constants.R_OK);
    return true;
  } catch {
    return false;
  }
}

async function requestFullDiskAccess(window) {
  const hasAccess = checkFullDiskAccess();
  if (hasAccess) return true;

  const result = await dialog.showMessageBox(window, {
    type: "info",
    title: "Full Disk Access Required",
    message: "Praxo-PICOS needs Full Disk Access to read your email and calendar data.",
    detail:
      "Click 'Open Settings' to grant access. In System Settings, find Praxo-PICOS in the list and toggle it on.\n\n" +
      "This permission stays on your Mac and is never shared.",
    buttons: ["Open Settings", "Skip for Now"],
    defaultId: 0,
    cancelId: 1,
  });

  if (result.response === 0) {
    shell.openExternal(
      "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
    );
  }

  return false;
}

async function promptScreenRecording(window) {
  const result = await dialog.showMessageBox(window, {
    type: "info",
    title: "Screen Recording (Optional)",
    message: "Want to capture screen activity with Screenpipe?",
    detail:
      "If you use Screenpipe, macOS needs Screen Recording permission. This is optional.",
    buttons: ["Open Settings", "Skip"],
    defaultId: 1,
    cancelId: 1,
  });

  if (result.response === 0) {
    shell.openExternal(
      "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
    );
  }
}

module.exports = { checkFullDiskAccess, requestFullDiskAccess, promptScreenRecording };
