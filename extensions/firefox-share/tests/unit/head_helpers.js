const {classes: Cc, interfaces: Ci, utils: Cu} = Components;

function initializeAddon() {
  Cu.import("resource://gre/modules/Services.jsm");
  const env = Cc["@mozilla.org/process/environment;1"]
                .getService(Ci.nsIEnvironment);
  let srcdir = Cc["@mozilla.org/file/local;1"]
                 .createInstance(Ci.nsILocalFile);
  srcdir.initWithPath(env.get("TOPDIR"));
  srcdir.append("src");

  let bootstrapNS = {
    APP_STARTUP    : 1,
    APP_SHUTDOWN   : 2,
    ADDON_ENABLE   : 3,
    ADDON_DISABLE  : 4,
    ADDON_INSTALL  : 5,
    ADDON_UNINSTALL: 6,
    ADDON_UPGRADE  : 7,
    ADDON_DOWNGRADE: 8
  };

  let bootstrapFile = srcdir.clone();
  bootstrapFile.append("bootstrap.js");
  let bootstrapFileURI = Services.io.newFileURI(bootstrapFile);

  const scriptLoader = Cc["@mozilla.org/moz/jssubscript-loader;1"]
                         .getService(Ci.mozIJSSubScriptLoader);
  scriptLoader.loadSubScript(bootstrapFileURI.spec, bootstrapNS);

  bootstrapNS.startup({
    id: "ffshare@mozilla.org",
    version: "42",
    installPath: srcdir
  }, bootstrapNS.APP_STARTUP);
}
initializeAddon();
