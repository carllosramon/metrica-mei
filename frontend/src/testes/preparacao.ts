import '@testing-library/jest-dom/vitest'

// O jsdom não implementa scrollIntoView, e a tela de detalhe usa isso
// para levar o usuário até o formulário que acabou de abrir. Sem o
// substituto, a chamada estoura no teste por falta de navegador, não por
// defeito do código.
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}
