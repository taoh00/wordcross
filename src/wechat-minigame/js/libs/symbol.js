/**
 * Symbol polyfill for older JavaScript environments
 */

if (typeof Symbol === 'undefined' && typeof GameGlobal !== 'undefined') {
  GameGlobal.Symbol = function(description) {
    return '__symbol_' + description + '_' + Math.random().toString(36).substr(2, 9)
  }
  GameGlobal.Symbol.iterator = '__symbol_iterator__'
}

module.exports = {}
