const assert=require('node:assert/strict');
module.exports=async function checkLayout(page,loggedIn) {
  await page.locator('#grid .slot').first().waitFor({state:'visible'});
  const previous=page.viewportSize();
  for(const viewport of [{width:1280,height:900},{width:390,height:844}]) {
    await page.setViewportSize(viewport);await page.evaluate(()=>window.scrollTo(0,0));
    const geometry=await page.evaluate(()=>{
      const box=selector=>document.querySelector(selector).getBoundingClientRect();
      const access=box('.account-access'),first=box('#grid .slot'),main=box('main'),workspace=box('#worker-workspace');
      return {accessHeight:access.height,firstSlot:first.top,mainBottom:main.bottom,
        workspaceTop:workspace.top,workspaceHidden:document.getElementById('worker-workspace').hidden,
        overflow:document.documentElement.scrollWidth>innerWidth,viewportHeight:innerHeight,
        headerContainsAccount:document.querySelector('header').contains(document.getElementById('account-form'))};
    });
    assert(geometry.headerContainsAccount);
    assert(geometry.accessHeight<=110,'Account controls must stay compact');
    assert(geometry.firstSlot>0 && geometry.firstSlot<geometry.viewportHeight/2,'Slots must appear near the top of the page');
    assert(!geometry.overflow,'No horizontal overflow on mobile or desktop');
    assert.equal(geometry.workspaceHidden,!loggedIn);
    if(loggedIn)assert(geometry.workspaceTop>=geometry.mainBottom-1,'Worker tools must follow all slots');
  }
  await page.setViewportSize(previous);await page.evaluate(()=>window.scrollTo(0,0));
};
