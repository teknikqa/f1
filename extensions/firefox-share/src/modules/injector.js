/* ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 *
 * The Original Code is People.
 *
 * The Initial Developer of the Original Code is Mozilla.
 * Portions created by the Initial Developer are Copyright (C) 2009
 * the Initial Developer. All Rights Reserved.
 *
 * Contributor(s):
 *   Shane Caraveo <shane@caraveo.com>
 *   Myk Melez <myk@mozilla.org>
 *   Justin Dolske <dolske@mozilla.com>
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** */

/* Inject the People content API into window.navigator objects. */
/* Partly based on code in the Geode extension. */

const Cc = Components.classes;
const Ci = Components.interfaces;
const Cu = Components.utils;
Cu.import("resource://gre/modules/XPCOMUtils.jsm");

let EXPORTED_SYMBOLS = ["Injector"];

const ALL_GROUP_CONSTANT = "___all___";
let refreshed;

let Injector = {
  // Injector will inject code into the browser content.  The provider class
  // looks like:
  
  //  var someapiprovider = {
  //    apibase: null, // null == 'navigator.mozilla.labs', or define your own namespace
  //    name: 'my_fn_name', // builds to 'navigator.mozilla.labs.my_fn_name'
  //    script: null, // null == use injected default script or provide your own
  //    getapi: function() {
  //      let someobject = somechromeobject;
  //      return function() {
  //        someobject();
  //      }
  //    }
  //  }
  //  Injector.register(someapiprovider);
  //
  //  With the above object, there would be a new api in content that can
  //  be used from any webpage like:
  //
  //  navigator.mozilla.labs.my_fn_name();
  
  providers: [],

  observe: function(aSubject, aTopic, aData) {
    if (!aSubject.location.href) return;
    for (var i in this.providers) {
      //dump("injecting api "+this.providers[i].name+"\n");
      this._inject(aSubject, this.providers[i]);
    }
  },
  
  register: function(provider) {
    //dump("registering api "+provider.name+"\n");
    this.providers.push(provider);
  },

  //**************************************************************************//
  // 

  SCRIPT_TO_INJECT_URI: "resource://ffshare/modules/injected.js",

  get _theScript() {
    delete this._theScript;
    ioSvc = Cc["@mozilla.org/network/io-service;1"].
                        getService(Ci.nsIIOService);
    let uri = ioSvc.newURI(this.SCRIPT_TO_INJECT_URI, null, null).QueryInterface(Ci.nsIFileURL);

    // Slurp the contents of the file into a string.
    let inputStream = Cc["@mozilla.org/network/file-input-stream;1"].
                      createInstance(Ci.nsIFileInputStream);
    inputStream.init(uri.file, 0x01, -1, null); // RD_ONLY
    let lineStream = inputStream.QueryInterface(Ci.nsILineInputStream);
    let line = { value: "" }, hasMore, scriptToInject = "";
    do {
        hasMore = lineStream.readLine(line);
        scriptToInject += line.value + "\n";
    } while (hasMore);
    lineStream.close();

    return this._theScript = scriptToInject;
  },
  
  _scriptToInject: function(provider) {
    // a provider may use it's own script to inject its api
    if (provider.script)
      return provider.script;
    // otherwise, use a builtin injector script that we load above
    let script = this._theScript;
    let apibase = provider.apibase ? provider.apibase : 'navigator.mozilla.labs';
    script = script.replace(/__API_BASE__/g, apibase)
                  .replace(/__API_NAME__/g, provider.name)
                  .replace(/__API_INJECTED__/g, '__mozilla_injected_api_'+provider.name+'__');
    //dump(script+"\n");
    return script;
  },

  /*
   * _inject
   *
   * Injects the content API into the specified DOM window.
   */
  _inject: function(win, provider) {
    // ensure we're dealing with a wrapped native
    var safeWin = new XPCNativeWrapper(win);
    // options here are ignored for 3.6
    let sandbox = new Cu.Sandbox(safeWin, { sandboxProto: safeWin, wantXrays: true });
    sandbox.importFunction(provider.getapi(), '__mozilla_injected_api_'+provider.name+'__');
    sandbox.window = safeWin;
    sandbox.navigator = safeWin.navigator.wrappedJSObject;
    Cu.evalInSandbox(this._scriptToInject(provider), sandbox, "1.8");
    //dump("injected api "+provider.name+": "+sandbox.navigator.mozilla.labs+"\n");
  }

};

var obs = Cc["@mozilla.org/observer-service;1"].getService(Ci.nsIObserverService);
obs.addObserver(Injector, 'content-document-global-created', false);
