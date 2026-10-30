const assert=require('node:assert/strict');
module.exports=async function checkLayout(page,loggedIn) {
  const previous=page.viewportSize(), previousView=await page.evaluate(()=>document.body.dataset.view);
  for(const viewport of [{width:1280,height:900},{width:390,height:844}]) {
    await page.setViewportSize(viewport);await page.evaluate(()=>{window.scrollTo(0,0);openView('overview');});
    const geometry=await page.evaluate(()=>({
      overflow:document.documentElement.scrollWidth>innerWidth,
      workspaceHidden:document.getElementById('worker-workspace').hidden,
      accountFormHidden:document.getElementById('account-form').hidden,
      overviewVisible:!document.querySelector('[data-page="overview"]').hidden,
      mobileMenu:getComputedStyle(document.getElementById('mobile-menu')).display!=='none',
    }));
    assert(!geometry.overflow,'No horizontal overflow on mobile or desktop');
    assert.equal(geometry.workspaceHidden,!loggedIn);
    assert.equal(geometry.accountFormHidden,loggedIn);
    assert(geometry.overviewVisible);
    assert.equal(geometry.mobileMenu,viewport.width<=760);
  }
  await page.setViewportSize(previous);await page.evaluate(view=>{window.scrollTo(0,0);openView(view);},previousView);
};
