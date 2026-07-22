function buildErrorDiagnostic(error = {}) {
  return {
    requestId: String(error.requestId || ""),
    clientVersion: String(error.clientVersion || ""),
    serviceVersion: String(error.serviceVersion || ""),
    buildId: String(error.buildId || ""),
    occurredAt: String(error.occurredAt || new Date().toISOString()),
  };
}

function buildErrorDiagnosticText(error = {}) {
  const item = buildErrorDiagnostic(error);
  return [
    `请求编号：${item.requestId || "未返回"}`,
    `客户端版本：${item.clientVersion || "未知"}`,
    `服务版本：${item.serviceVersion || "未知"}`,
    `构建编号：${item.buildId || "未知"}`,
    `发生时间：${item.occurredAt}`,
  ].join("\n");
}

function copyErrorDiagnostic(error = {}) {
  return new Promise((resolve, reject) => {
    wx.setClipboardData({
      data: buildErrorDiagnosticText(error),
      success: resolve,
      fail: reject,
    });
  });
}

module.exports = {
  buildErrorDiagnostic,
  buildErrorDiagnosticText,
  copyErrorDiagnostic,
};
