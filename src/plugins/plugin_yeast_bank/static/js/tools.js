(() => {
  "use strict";

  /**
   * Compatibilidade legada.
   * -----------------------------------------------------------------
   * A tela de ferramentas foi unificada em starters.html e o comportamento
   * principal agora vive em static/js/starters.js.
   *
   * Este arquivo é mantido apenas para evitar erro em instalações antigas
   * que ainda referenciem tools.js. Se ele for carregado isoladamente, registra
   * apenas um aviso no console.
   */
  console.warn("[YeastBank:Tools] tools.js está em modo de compatibilidade. Use starters.js na tela unificada Starter & Contagem.");
})();
