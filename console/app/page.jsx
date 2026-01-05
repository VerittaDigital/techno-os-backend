export const metadata = {
  title: 'VERITTÀ TECHNO OS',
  description: 'Private Access · January 2026',
}

export default function Home() {
  return (
    <main style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      lineHeight: '1.6',
      color: '#1a1a1a',
      backgroundColor: '#ffffff',
    }}>
      <div style={{ maxWidth: '600px', textAlign: 'center' }}>
        <h1 style={{
          fontSize: '2.5rem',
          fontWeight: '300',
          marginBottom: '0.5rem',
          letterSpacing: '0.05em',
        }}>
          VERITTÀ TECHNO OS
        </h1>

        <p style={{
          fontSize: '0.95rem',
          color: '#666',
          marginBottom: '2rem',
          fontWeight: '300',
        }}>
          Private Access · January 2026
        </p>

        <section style={{
          marginBottom: '2.5rem',
          paddingBottom: '2rem',
          borderBottom: '1px solid #e5e5e5',
        }}>
          <p style={{
            fontSize: '1rem',
            lineHeight: '1.8',
            marginBottom: '1.5rem',
          }}>
            O beta de Verittà Techno OS é uma visualização técnica governada e informacional do sistema. 
            Acesso controlado e auditorado.
          </p>

          <p style={{
            fontSize: '0.9rem',
            color: '#888',
            fontStyle: 'italic',
          }}>
            Sem formulários. Sem coleta de dados. Sem rastreamento.
          </p>
        </section>

        <div style={{
          marginBottom: '2rem',
        }}>
          <style>{`
            a.cta-button:hover {
              opacity: 0.8;
            }
          `}</style>
          <a
            href="/beta"
            className="cta-button"
            style={{
              display: 'inline-block',
              padding: '0.75rem 1.5rem',
              backgroundColor: '#000',
              color: '#fff',
              textDecoration: 'none',
              fontSize: '0.95rem',
              fontWeight: '500',
              letterSpacing: '0.05em',
              border: 'none',
              cursor: 'pointer',
              transition: 'opacity 0.2s',
            }}
          >
            Acessar Beta →
          </a>
        </div>

        <footer style={{
          marginTop: '3rem',
          paddingTop: '2rem',
          borderTop: '1px solid #e5e5e5',
          fontSize: '0.85rem',
          color: '#999',
        }}>
          <p>
            Para quem entende antes do mercado.
          </p>
        </footer>
      </div>
    </main>
  )
}
