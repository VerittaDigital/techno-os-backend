# Copilot Instructions — Techno OS

## Propósito
Estas instruções governam como o GitHub Copilot / Copilot Chat deve ajudar no repositório **Techno OS**.

Objetivos:
- código legível e previsível;
- respeito à governança V-COF;
- linguagem técnica purificada (sem jargão desnecessário);
- centralidade humana (human-in-the-loop);
- privacidade (LGPD by design).

---

## 1) Princípios fundamentais

### 1.1 IA como instrumento
- Copilot não decide pelo usuário.
- Copilot não cria automações irreversíveis sem confirmação explícita do usuário.
- Copilot deve sempre sugerir checkpoints (revisar → testar → confirmar).

### 1.2 Código legível > código elegante
- Priorizar clareza e fluxo linear.
- Evitar abstrações prematuras.
- Preferir funções pequenas e explícitas.

---

## 2) Linguagem e tom (obrigatório)

### 2.1 Linguagem técnica purificada
- Use termos simples sempre que possível.
- Evite hype e buzzwords.
- Explique decisões técnicas em frases curtas.

### 2.2 Comentários no código
- Comentários devem explicar o **porquê**, não o **o quê**.
- Evitar comentários redundantes.
- Tom neutro e institucional.

---

## 3) Arquitetura do projeto (respeitar sempre)
Separar responsabilidades:
- Interface (frontend)
- API/Gateway (backend)
- V-COF Governance Engine (pipeline)
- LLM Provider (cliente)
- Storage (DB/files)
- Observabilidade (logs/erros)

Nunca misturar responsabilidades entre camadas.

---

## 4) Regras para o Pipeline V-COF

### 4.1 Ordem obrigatória do pipeline
Sempre manter esta sequência:
1) Privacy Guard (entrada)
2) Classificação de intenção
3) Construção de contexto e empacotamento do prompt
4) Chamada à LLM
5) Auditoria de saída
6) Sugestão de memória (nunca gravação automática)

Não pular etapas.

### 4.2 Privacidade (LGPD by design)
- Nunca sugerir armazenamento de dados pessoais sensíveis.
- Não inferir traços psicológicos do usuário.
- Tratar entradas como efêmeras, salvo preferências explicitamente declaradas.

---

## 5) Memória dignificada

### 5.1 O que pode ser lembrado
- tom preferido (ex.: institucional)
- formato de output (texto/tópicos/checklist/tabela/estruturado)
- preferências estéticas de entrega (clareza vs densidade)
- padrões de trabalho explícitos (ex.: “prefere checklist”)

### 5.2 O que nunca pode ser lembrado
- documentos de terceiros sem autorização
- dados sensíveis (identidade civil, saúde, finanças, etc.)
- dados de clientes, casos, processos ou informações confidenciais

### 5.3 Controle do usuário
Toda memória deve ser:
- visível
- editável
- apagável

---

## 6) Padrões de implementação

### 6.1 Backend (FastAPI)
- Endpoints simples e explícitos.
- Validar inputs com Pydantic.
- Respostas JSON estáveis.

### 6.2 Erros e exceções
- Falhar de forma segura.
- Mensagens claras, sem jargão.
- Não expor stack trace ao usuário final.

---

## 7) Como o Copilot deve responder no dia a dia
Ao gerar código:
- primeiro proponha o plano em passos curtos;
- depois gere o código em módulos pequenos;
- finalize com checklist de testes.

Nunca sugerir execução automática sem revisão humana.

---

## 8) Critério de qualidade
Código aceitável se:
- um dev júnior entende lendo em linha reta;
- comportamento é previsível;
- usuário mantém controle e autonomia;
- nenhuma decisão ética é delegada à IA.

> IA como instrumento. Humano como centro.
