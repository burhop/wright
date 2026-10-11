import importlib.util
spec=importlib.util.spec_from_file_location('selected_addon','/selected/provider-source/addon.py')
addon=importlib.util.module_from_spec(spec)
spec.loader.exec_module(addon)
addon.register()
server=addon.BlenderMCPServer(host='127.0.0.1',port=19988)
server.start()
assert server.running
print('OWNED_BLENDER_READY',flush=True)
