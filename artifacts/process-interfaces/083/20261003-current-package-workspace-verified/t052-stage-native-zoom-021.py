"""Preserve020; inspect actual frame and scroll geometry after native zoom."""
from pathlib import Path

base = Path('D:/repos/wright/.local-run/process-interfaces-083')
target = base / 't052-native-zoom-021.mjs'
assert not target.exists()
text = (base / 't052-native-zoom-020.mjs').read_text(encoding='utf-8')
text = text.replace('-020', '-021').replace("'zoom-extension-020'", "'zoom-extension-021'").replace("'zoom-browser-profile-020'", "'zoom-browser-profile-021'")
needle = "  await expect(previewFrame.getByText('Preview - process controls are read-only.',{exact:true})).toBeVisible();"
assert needle in text
text = text.replace(needle, """  const afterZoomFrames=[];
  for(const currentFrame of page.frames()){
    afterZoomFrames.push(await currentFrame.evaluate(()=>({url:location.href,body:document.body?.innerText.slice(0,3000),innerWidth,innerHeight,devicePixelRatio,pageScale:visualViewport?.scale})).catch(error=>({error:error.message})));
  }
  const afterZoomBoxes=await previewView.evaluate(root=>({root:root.getBoundingClientRect().toJSON(),clientHeight:root.clientHeight,scrollHeight:root.scrollHeight,scrollTop:root.scrollTop,frame:root.querySelector('iframe')?.getBoundingClientRect().toJSON(),frameSrc:root.querySelector('iframe')?.src}));
  writeFileSync(path.join(privateRoot,'zoom021-after-zoom-geometry.json'),JSON.stringify({afterZoomFrames,afterZoomBoxes},null,2));
  await previewView.getByTestId('surface-panel-host').scrollIntoViewIfNeeded();
  await expect(previewFrame.getByText('Preview - process controls are read-only.',{exact:true})).toBeVisible();""")
target.write_text(text, encoding='utf-8')
print('Prepared021 frame/layout diagnostics and explicit normal scroll after browser zoom;020 retained.')
