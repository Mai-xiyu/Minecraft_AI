module.exports = function buildIndexFromArray (array, fieldToIndex) {
  if (array === undefined) { return undefined }
  return array.reduce(function (index, element) {
    index[element[fieldToIndex]] = element
    return index
  }, {})
}
