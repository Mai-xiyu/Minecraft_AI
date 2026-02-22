module.exports = format

function format (string, _with = []) {
  let i = 0

  return string.replace(/%(?:(\d+)\$)?(s|%)/g, (g0, g1) => {
    if (g0 === '%%') {
      return '%'
    } else {
      const idx = g1 ? parseInt(g1) - 1 : i++
      if (_with[idx] !== undefined) {
        return _with[idx]
      } else {
        return ''
      }
    }
  })
}
