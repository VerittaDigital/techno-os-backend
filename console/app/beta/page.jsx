export default function BetaPage() {
  return (
    <main className="min-h-screen bg-white text-gray-900">
      {/* HERO (acima da dobra) */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-5xl font-bold mb-4">Governança antes da resposta.</h1>

          <h2 className="text-xl text-gray-700 mb-6">
            O Verittà Techno OS é um console governado.
            <br />
            Ele não executa IA — ele governa a interação humana com sistemas de decisão.
          </h2>

          <div className="text-gray-600 mb-8 space-y-2">
            <p>Você verá bloqueios.</p>
            <p>Você verá descartes de respostas fora de contexto.</p>
            <p>Você verá evidência — explicitamente rotulada quando for local.</p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button className="px-8 py-3 bg-black text-white rounded font-semibold hover:bg-gray-800">
              Solicitar convite para o Beta Público Controlado
            </button>
            <a href="#como-funciona" className="px-8 py-3 text-gray-900 hover:underline">
              Ler como funciona (2 minutos)
            </a>
          </div>

          <div className="text-sm text-gray-500">
            Fail-closed · Determinismo · Privacidade por design · Human-in-the-loop
          </div>
        </div>
      </section>

      {/* BLOCO 1 — O QUE VOCÊ RECEBE */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-8">O que este sistema entrega (de verdade)</h2>

          <ul className="space-y-3 mb-6 text-gray-700">
            <li>• Um fluxo determinístico: mesma entrada → mesma saída (quando permitido)</li>
            <li>• Um modelo fail-closed: quando não é seguro, não executa</li>
            <li>• Contexto explícito: o sistema impede mistura entre "work", "test", "sandbox"</li>
            <li>• Proteção contra corridas: apenas a última execução vale (Newest-Wins)</li>
            <li>• Rastreabilidade por eventos e trace_id (quando disponível no backend)</li>
          </ul>

          <p className="text-sm text-gray-600 italic">
            Aqui, "não aplicar" é uma decisão governada — não um bug.
          </p>
        </div>
      </section>

      {/* BLOCO 2 — O QUE ESTE SISTEMA NÃO É */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-8">O que isso não é</h2>

          <ul className="space-y-3 mb-6 text-gray-700">
            <li>• Não é ChatGPT</li>
            <li>• Não é um chat recreativo</li>
            <li>• Não promete respostas sempre úteis</li>
            <li>• Não "improvisa" quando falta evidência</li>
            <li>• Não simula auditoria backend inexistente</li>
          </ul>

          <p className="text-gray-900 font-semibold">
            Se você precisa que o sistema sempre responda, este Beta não é para você.
          </p>
        </div>
      </section>

      {/* BLOCO 3 — COMO FUNCIONA (passo a passo) */}
      <section id="como-funciona" className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-8">Como funciona o Beta Público Controlado</h2>

          <ol className="space-y-4 mb-8 text-gray-700">
            <li>
              <strong>1. Você recebe uma API Key própria (backend)</strong>
            </li>
            <li>
              <strong>2. Declara seu user_id (identidade operacional)</strong>
            </li>
            <li>
              <strong>3. Escolhe um context_id (ex.: work / test / sandbox)</strong>
            </li>
            <li>
              <strong>4. Executa — e o sistema faz duas coisas:</strong>
              <ul className="ml-6 mt-2 space-y-1">
                <li>• aplica apenas resultados válidos no contexto atual</li>
                <li>• descarta respostas incorretas/antigas com evento explícito</li>
              </ul>
            </li>
          </ol>

          <div className="border-l-4 border-gray-900 pl-6 py-4 bg-white">
            <p className="font-semibold mb-3">Você verá eventos como:</p>
            <p className="text-gray-700">
              <strong>CONTEXT_SWITCH_DROPPED</strong> — contexto mudou durante execução
              <br />
              <strong>STALE_RESPONSE_DROPPED</strong> — resposta antiga descartada (Newest-Wins)
              <br />
              <strong>SUCCESS / FAILED / BLOCKED</strong> — estado final
            </p>
          </div>
        </div>
      </section>

      {/* BLOCO 4 — AUDITORIA (verdade dura, transparente) */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-8">Auditoria neste Beta: sem teatro</h2>

          <p className="text-gray-700 mb-6">
            Quando não existir endpoint de auditoria no backend, o Audit Viewer opera em modo Local Stub:
            evidência local, rotulada explicitamente como "not backend audit", com TTL e isolamento por user_id + context_id.
          </p>

          <ul className="space-y-3 text-gray-700">
            <li>• Evidência local não é prova de isolamento backend</li>
            <li>• É prova de governança de superfície e integridade de UX</li>
            <li>• Transparência total: a fonte é sempre indicada</li>
          </ul>
        </div>
      </section>

      {/* BLOCO 5 — PRINCÍPIOS INEGOCIÁVEIS */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-8">Princípios inegociáveis</h2>

          <p className="text-gray-900 font-semibold mb-4">
            Fail-closed. Determinismo. Privacidade por design.
          </p>

          <p className="text-gray-900 font-semibold">
            Human-in-the-loop. Governança explícita. Zero heurística silenciosa.
          </p>
        </div>
      </section>

      {/* BLOCO 6 — PARA QUEM É ESTE BETA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-8">Este Beta é para você se:</h2>

          <ul className="space-y-3 mb-8 text-gray-700">
            <li>• Você prefere entender o porquê a receber qualquer resposta</li>
            <li>• Você aceita bloqueios como parte do sistema</li>
            <li>• Você trabalha com decisão, risco, responsabilidade ou sistemas críticos</li>
            <li>• Você quer ver governança funcionando — não apenas prometida</li>
          </ul>

          <p className="text-gray-900 font-semibold">
            Se você busca velocidade sem controle, não avance.
          </p>
        </div>
      </section>

      {/* DISCLAIMER */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-yellow-50 border-t-4 border-yellow-200">
        <div className="max-w-3xl mx-auto">
          <p className="text-gray-800 mb-3">
            Este sistema pode bloquear, recusar ou retornar vazio.
            Isso não configura erro.
            A auditoria exibida neste Beta é local e explicitamente rotulada quando não corresponde a auditoria backend.
            A responsabilidade final pelas decisões permanece sempre humana.
          </p>
        </div>
      </section>

      {/* CTA FINAL */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-900 text-white text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Beta Público Controlado. Curadoria manual.</h2>
          <p className="text-gray-300 mb-8">
            Convites são analisados manualmente. Participação não implica roadmap futuro.
          </p>
          <button className="px-8 py-3 bg-white text-gray-900 rounded font-semibold hover:bg-gray-200">
            Solicitar convite
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-100 text-center text-gray-700 text-sm">
        <p className="font-semibold mb-2">Verittà Techno OS</p>
        <p>Beta Público Controlado · Dezembro / 2025</p>
        <p>Governança explícita · Sem promessas falsas</p>
      </footer>
    </main>
  );
}
