# Landing v1.0 — Verittà Techno OS Beta Público Controlado

## HERO (acima da dobra)

### H1
Governança antes da resposta.

### H2
O Verittà Techno OS é um console governado.
Ele não executa IA — ele governa a interação humana com sistemas de decisão.

### Microcopy (3 linhas)
Você verá bloqueios.
Você verá descartes de respostas fora de contexto.
Você verá evidência — explicitamente rotulada quando for local.

### CTA primário
Solicitar convite para o Beta Público Controlado

### CTA secundário (link discreto)
Ler como funciona (2 minutos)

### Linha de credencial (pequena, sem hype)
Fail-closed · Determinismo · Privacidade por design · Human-in-the-loop


## BLOCO 1 — O QUE VOCÊ RECEBE

### Título
O que este sistema entrega (de verdade)

### Bullets
• Um fluxo determinístico: mesma entrada → mesma saída (quando permitido)
• Um modelo fail-closed: quando não é seguro, não executa
• Contexto explícito: o sistema impede mistura entre "work", "test", "sandbox"
• Proteção contra corridas: apenas a última execução vale (Newest-Wins)
• Rastreabilidade por eventos e trace_id (quando disponível no backend)

### Nota (1 linha)
Aqui, "não aplicar" é uma decisão governada — não um bug.


## BLOCO 2 — O QUE ESTE SISTEMA NÃO É

### Título
O que isso não é

### Bullets (negativas, curtas)
• Não é ChatGPT
• Não é um chat recreativo
• Não promete respostas sempre úteis
• Não "improvisa" quando falta evidência
• Não simula auditoria backend inexistente

### Linha de corte
Se você precisa que o sistema sempre responda, este Beta não é para você.


## BLOCO 3 — COMO FUNCIONA (passo a passo)

### Título
Como funciona o Beta Público Controlado

### Passos (numerados)
1. Você recebe uma API Key própria (backend)
2. Declara seu user_id (identidade operacional)
3. Escolhe um context_id (ex.: work / test / sandbox)
4. Executa — e o sistema faz duas coisas:
   • aplica apenas resultados válidos no contexto atual
   • descarta respostas incorretas/antigas com evento explícito

### Destaque técnico (caixa)
Você verá eventos como:
CONTEXT_SWITCH_DROPPED — contexto mudou durante execução
STALE_RESPONSE_DROPPED — resposta antiga descartada (Newest-Wins)
SUCCESS / FAILED / BLOCKED — estado final


## BLOCO 4 — AUDITORIA (verdade dura, transparente)

### Título
Auditoria neste Beta: sem teatro

### Texto
Quando não existir endpoint de auditoria no backend, o Audit Viewer opera em modo Local Stub:
evidência local, rotulada explicitamente como "not backend audit", com TTL e isolamento por user_id + context_id.

### Bullets (claros)
• Evidência local não é prova de isolamento backend
• É prova de governança de superfície e integridade de UX
• Transparência total: a fonte é sempre indicada


## BLOCO 5 — PRINCÍPIOS INEGOCIÁVEIS

### Título
Princípios inegociáveis

### Linha 1
Fail-closed. Determinismo. Privacidade por design.

### Linha 2
Human-in-the-loop. Governança explícita. Zero heurística silenciosa.


## BLOCO 6 — PARA QUEM É ESTE BETA

### Título
Este Beta é para você se:

### Bullets
• Você prefere entender o porquê a receber qualquer resposta
• Você aceita bloqueios como parte do sistema
• Você trabalha com decisão, risco, responsabilidade ou sistemas críticos
• Você quer ver governança funcionando — não apenas prometida


### Linha de exclusão
Se você busca velocidade sem controle, não avance.


## DISCLAIMER (visível, obrigatório)

Este sistema pode bloquear, recusar ou retornar vazio.
Isso não configura erro.
A auditoria exibida neste Beta é local e explicitamente rotulada quando não corresponde a auditoria backend.
A responsabilidade final pelas decisões permanece sempre humana.


## CTA FINAL

### Título
Beta Público Controlado. Curadoria manual.

### Texto
Convites são analisados manualmente. Participação não implica roadmap futuro.

### Botão/Link
Solicitar convite


## FOOTER

Verittà Techno OS
Beta Público Controlado · Dezembro / 2025
Governança explícita · Sem promessas falsas
