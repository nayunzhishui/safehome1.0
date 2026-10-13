// Custom-navigation metrics for the tab pages (Figma P3/NavBar 620:7: status bar 44 + nav 44).
// Everything is in px, measured from the WeChat capsule so content lines up on every device.
const FIGMA_NAV_BOTTOM = 88;

function readWindow() {
  try {
    if (wx.getWindowInfo) return wx.getWindowInfo();
    return wx.getSystemInfoSync();
  } catch (error) {
    return {};
  }
}

function readCapsule() {
  try {
    return wx.getMenuButtonBoundingClientRect ? wx.getMenuButtonBoundingClientRect() : null;
  } catch (error) {
    return null;
  }
}

function navMetrics() {
  const info = readWindow();
  const statusBar = Number(info.statusBarHeight) || 44;
  const capsule = readCapsule();
  const valid = capsule && capsule.height > 0 && capsule.top >= statusBar;
  const capsuleTop = valid ? capsule.top : statusBar + 6;
  const capsuleHeight = valid ? capsule.height : 32;
  const navBottom = valid ? capsule.bottom + (capsule.top - statusBar) : statusBar + 44;
  return {
    statusBar,
    capsuleTop,
    capsuleHeight,
    capsuleCenter: capsuleTop + capsuleHeight / 2,
    navBottom,
    // How far the real navigation bar sits below the Figma one; hero art is shifted by this much.
    offset: navBottom - FIGMA_NAV_BOTTOM,
  };
}

module.exports = { navMetrics, FIGMA_NAV_BOTTOM };
