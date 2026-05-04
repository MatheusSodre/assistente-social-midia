const PLANS = [
  {
    name: 'Starter',
    price: 97,
    description: 'Para quem está começando nas redes sociais',
    color: '#28a745',
    features: [
      '15 posts por mês',
      'Post e Story',
      '1 business',
      '1 conta Instagram',
      'Sofia (Diretora Criativa)',
      'Geração de imagem IA',
      'Calendário editorial',
      'Suporte por email',
    ],
    cta: 'Começar agora',
    popular: false,
  },
  {
    name: 'Pro',
    price: 197,
    description: 'Para negócios que querem crescer',
    color: '#6f42c1',
    features: [
      '50 posts por mês',
      'Post, Story, Reel e Carrossel',
      '3 businesses',
      '3 contas Instagram',
      'Sofia + Mara + Pixel',
      'Análise de estilo do feed',
      'Identidade visual IA',
      'Métricas de engajamento',
      'Suporte por WhatsApp',
    ],
    cta: 'Escolher Pro',
    popular: true,
  },
  {
    name: 'Premium',
    price: 497,
    description: 'Para agências e marcas que dominam',
    color: '#fd7e14',
    features: [
      'Posts ilimitados',
      'Todos os formatos',
      '10 businesses',
      '10 contas Instagram',
      'Todos os agentes (+ Luna Ads)',
      'Google Ads integrado',
      'Templates por nicho',
      'Gestão financeira',
      'Suporte prioritário',
    ],
    cta: 'Falar com vendas',
    popular: false,
  },
]

const FEATURES = [
  {
    icon: 'fas fa-robot',
    title: '4 Agentes de IA',
    description: 'Sofia (Diretora Criativa), Mara (Social Media), Pixel (Designer) e Luna (Google Ads) trabalham juntos pela sua marca.',
  },
  {
    icon: 'fas fa-image',
    title: 'Imagens Cinematográficas',
    description: 'Geração de imagens com qualidade de campanha publicitária. Prompts profissionais que criam visuais que param o scroll.',
  },
  {
    icon: 'fas fa-images',
    title: 'Carrossel Inteligente',
    description: 'Carrosséis de 2 a 10 slides com narrativa sequencial. Cada slide conta parte da história.',
  },
  {
    icon: 'fas fa-check-double',
    title: 'Aprovação Antes de Postar',
    description: 'Nada é publicado sem a sua aprovação. Preview em mockup do Instagram antes de confirmar.',
  },
  {
    icon: 'fas fa-calendar-alt',
    title: 'Calendário Editorial',
    description: 'Agende publicações, visualize a semana e o mês. Nunca mais esqueça de postar.',
  },
  {
    icon: 'fas fa-palette',
    title: 'Identidade Visual IA',
    description: 'Pixel aprende suas cores, fontes e estilo. Cada post segue sua identidade de marca.',
  },
]

const STEPS = [
  { number: '1', title: 'Conecte seu negócio', description: 'Cadastre sua empresa e conecte o Instagram. A IA analisa seu perfil em segundos.' },
  { number: '2', title: 'Sofia cria conteúdo', description: 'Diga o que precisa e a Sofia coordena toda a equipe criativa para gerar posts prontos.' },
  { number: '3', title: 'Aprove e publique', description: 'Revise com preview real do Instagram. Aprovou? Publicamos direto no seu perfil.' },
]

interface LandingPageProps {
  onLogin: () => void
}

export function LandingPage({ onLogin }: LandingPageProps) {
  return (
    <div style={{ fontFamily: "'Segoe UI', -apple-system, sans-serif", color: '#1a1a2e', background: '#fff' }}>
      {/* Navbar */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
        background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)',
        borderBottom: '1px solid #eee', padding: '12px 0',
      }}>
        <div className="container d-flex align-items-center justify-content-between">
          <div className="d-flex align-items-center" style={{ gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontWeight: 800, fontSize: 16,
            }}>O</div>
            <span style={{ fontWeight: 700, fontSize: 20, color: '#1a1a2e' }}>
              Orbita<span style={{ color: '#6f42c1' }}>.IA</span>
            </span>
          </div>
          <div className="d-flex align-items-center" style={{ gap: 16 }}>
            <a href="#features" style={{ color: '#555', textDecoration: 'none', fontSize: 14, fontWeight: 500 }}>Funcionalidades</a>
            <a href="#pricing" style={{ color: '#555', textDecoration: 'none', fontSize: 14, fontWeight: 500 }}>Planos</a>
            <button
              onClick={onLogin}
              style={{
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                color: '#fff', border: 'none', borderRadius: 8,
                padding: '8px 20px', fontWeight: 600, fontSize: 14, cursor: 'pointer',
              }}
            >
              Entrar
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center',
        background: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
        color: '#fff', paddingTop: 80,
      }}>
        <div className="container">
          <div className="row align-items-center">
            <div className="col-lg-6 mb-4 mb-lg-0">
              <div style={{
                display: 'inline-block', background: 'rgba(111,66,193,0.2)',
                border: '1px solid rgba(111,66,193,0.4)', borderRadius: 20,
                padding: '4px 14px', fontSize: 13, marginBottom: 20, color: '#c4b5fd',
              }}>
                <i className="fas fa-bolt mr-1" /> Agência de IA para suas redes sociais
              </div>
              <h1 style={{ fontSize: 48, fontWeight: 800, lineHeight: 1.1, marginBottom: 20 }}>
                Sua equipe de marketing
                <br />
                <span style={{
                  background: 'linear-gradient(135deg, #667eea, #a78bfa, #f472b6)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}>
                  que nunca dorme.
                </span>
              </h1>
              <p style={{ fontSize: 18, color: '#b8b8d4', lineHeight: 1.7, marginBottom: 30, maxWidth: 480 }}>
                4 agentes de IA criam posts, stories e carrosséis com a cara da sua marca.
                Imagens profissionais, textos que vendem, publicação automática no Instagram.
              </p>
              <div className="d-flex flex-wrap" style={{ gap: 12 }}>
                <button
                  onClick={onLogin}
                  style={{
                    background: 'linear-gradient(135deg, #667eea, #764ba2)',
                    color: '#fff', border: 'none', borderRadius: 12,
                    padding: '14px 32px', fontWeight: 700, fontSize: 16, cursor: 'pointer',
                    boxShadow: '0 8px 30px rgba(102,126,234,0.4)',
                    transition: 'transform 0.2s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-2px)')}
                  onMouseLeave={e => (e.currentTarget.style.transform = '')}
                >
                  Testar gratis por 7 dias <i className="fas fa-arrow-right ml-2" />
                </button>
                <a
                  href="#how-it-works"
                  style={{
                    color: '#b8b8d4', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 12,
                    padding: '14px 24px', fontWeight: 500, fontSize: 15,
                    textDecoration: 'none', display: 'inline-flex', alignItems: 'center',
                  }}
                >
                  <i className="fas fa-play-circle mr-2" /> Como funciona
                </a>
              </div>
              <div className="d-flex align-items-center mt-4" style={{ gap: 16, color: '#8888aa' }}>
                <span style={{ fontSize: 13 }}><i className="fas fa-check mr-1" style={{ color: '#28a745' }} /> Sem cartao de credito</span>
                <span style={{ fontSize: 13 }}><i className="fas fa-check mr-1" style={{ color: '#28a745' }} /> Cancele quando quiser</span>
              </div>
            </div>
            <div className="col-lg-6 text-center">
              {/* Phone mockup */}
              <div style={{
                width: 300, margin: '0 auto',
                background: '#1a1a1a', borderRadius: 36, padding: 8,
                boxShadow: '0 30px 80px rgba(0,0,0,0.5)',
                transform: 'perspective(1000px) rotateY(-5deg)',
              }}>
                <div style={{ background: '#fff', borderRadius: 28, overflow: 'hidden', minHeight: 500 }}>
                  {/* IG header */}
                  <div style={{ padding: '10px 14px', borderBottom: '1px solid #eee', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 700, fontSize: 16, fontFamily: 'cursive', color: '#262626' }}>Instagram</span>
                    <div style={{ display: 'flex', gap: 12, color: '#262626' }}>
                      <i className="far fa-heart" />
                      <i className="far fa-paper-plane" />
                    </div>
                  </div>
                  {/* Fake post */}
                  <div style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: 'linear-gradient(45deg,#f09433,#dc2743,#bc1888)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#fff', fontSize: 10, fontWeight: 700,
                    }}>IA</div>
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#262626' }}>suamarca</span>
                    <span style={{ fontSize: 11, color: '#8e8e8e' }}>Patrocinado</span>
                  </div>
                  <div style={{
                    height: 280, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexDirection: 'column', color: '#fff',
                  }}>
                    <i className="fas fa-magic" style={{ fontSize: 48, marginBottom: 12, opacity: 0.8 }} />
                    <span style={{ fontSize: 14, fontWeight: 600 }}>Gerado por IA</span>
                    <span style={{ fontSize: 11, opacity: 0.7 }}>em 30 segundos</span>
                  </div>
                  <div style={{ padding: '8px 12px' }}>
                    <div style={{ display: 'flex', gap: 12, fontSize: 20, color: '#262626', marginBottom: 6 }}>
                      <i className="far fa-heart" />
                      <i className="far fa-comment" style={{ transform: 'scaleX(-1)' }} />
                      <i className="far fa-paper-plane" />
                    </div>
                    <p style={{ fontSize: 12, color: '#262626', margin: 0, lineHeight: 1.4 }}>
                      <strong>suamarca</strong> Caption impactante gerada pela Sofia...
                    </p>
                    <p style={{ fontSize: 11, color: '#00376b', margin: '4px 0 0' }}>
                      #marketing #ia #branding
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Logos / Social proof */}
      <section style={{ padding: '40px 0', background: '#f8f9fa', borderBottom: '1px solid #eee' }}>
        <div className="container text-center">
          <p style={{ fontSize: 13, color: '#999', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>
            Tecnologias que impulsionam nossa IA
          </p>
          <div className="d-flex justify-content-center align-items-center flex-wrap" style={{ gap: 32, opacity: 0.5, fontSize: 14, color: '#666' }}>
            <span><i className="fas fa-brain mr-1" /> Claude AI</span>
            <span><i className="fas fa-gem mr-1" /> Google Gemini</span>
            <span><i className="fab fa-instagram mr-1" /> Meta Graph API</span>
            <span><i className="fas fa-palette mr-1" /> DALL-E</span>
            <span><i className="fas fa-cloud mr-1" /> Cloudflare R2</span>
          </div>
        </div>
      </section>

      {/* Como funciona */}
      <section id="how-it-works" style={{ padding: '80px 0', background: '#fff' }}>
        <div className="container">
          <div className="text-center mb-5">
            <h2 style={{ fontSize: 36, fontWeight: 800, color: '#1a1a2e' }}>
              Simples como <span style={{ color: '#6f42c1' }}>1, 2, 3</span>
            </h2>
            <p style={{ color: '#666', fontSize: 16, maxWidth: 500, margin: '12px auto 0' }}>
              Da ideia ao Instagram em minutos, não em horas.
            </p>
          </div>
          <div className="row">
            {STEPS.map((step, i) => (
              <div key={i} className="col-md-4 mb-4">
                <div className="text-center">
                  <div style={{
                    width: 64, height: 64, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #667eea, #764ba2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontSize: 24, fontWeight: 800, margin: '0 auto 16px',
                  }}>
                    {step.number}
                  </div>
                  <h4 style={{ fontWeight: 700, fontSize: 18, color: '#1a1a2e' }}>{step.title}</h4>
                  <p style={{ color: '#666', fontSize: 14, lineHeight: 1.6 }}>{step.description}</p>
                </div>
                {i < 2 && (
                  <div className="d-none d-md-block text-center">
                    <i className="fas fa-chevron-right" style={{ color: '#ddd', fontSize: 24 }} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" style={{ padding: '80px 0', background: '#f8f9fa' }}>
        <div className="container">
          <div className="text-center mb-5">
            <h2 style={{ fontSize: 36, fontWeight: 800, color: '#1a1a2e' }}>
              Tudo que sua marca precisa.<br />
              <span style={{ color: '#6f42c1' }}>Numa unica plataforma.</span>
            </h2>
          </div>
          <div className="row">
            {FEATURES.map((f, i) => (
              <div key={i} className="col-md-4 mb-4">
                <div style={{
                  background: '#fff', borderRadius: 16, padding: 28,
                  height: '100%', border: '1px solid #eee',
                  transition: 'box-shadow 0.2s, transform 0.2s',
                  cursor: 'default',
                }}
                  onMouseEnter={e => {
                    e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.08)'
                    e.currentTarget.style.transform = 'translateY(-4px)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.boxShadow = ''
                    e.currentTarget.style.transform = ''
                  }}
                >
                  <div style={{
                    width: 48, height: 48, borderRadius: 12,
                    background: 'linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: 16,
                  }}>
                    <i className={f.icon} style={{ fontSize: 20, color: '#6f42c1' }} />
                  </div>
                  <h5 style={{ fontWeight: 700, fontSize: 16, color: '#1a1a2e', marginBottom: 8 }}>{f.title}</h5>
                  <p style={{ color: '#666', fontSize: 14, lineHeight: 1.6, margin: 0 }}>{f.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" style={{ padding: '80px 0', background: '#fff' }}>
        <div className="container">
          <div className="text-center mb-5">
            <h2 style={{ fontSize: 36, fontWeight: 800, color: '#1a1a2e' }}>
              Planos para cada <span style={{ color: '#6f42c1' }}>fase do seu negocio</span>
            </h2>
            <p style={{ color: '#666', fontSize: 16, maxWidth: 500, margin: '12px auto 0' }}>
              Comece gratis por 7 dias. Sem cartao de credito.
            </p>
          </div>
          <div className="row justify-content-center">
            {PLANS.map((plan, i) => (
              <div key={i} className="col-lg-4 col-md-6 mb-4">
                <div style={{
                  background: '#fff', borderRadius: 20, padding: 32,
                  border: plan.popular ? `2px solid ${plan.color}` : '1px solid #eee',
                  position: 'relative', height: '100%',
                  display: 'flex', flexDirection: 'column',
                  boxShadow: plan.popular ? `0 12px 40px rgba(111,66,193,0.15)` : '',
                  transform: plan.popular ? 'scale(1.03)' : '',
                }}>
                  {plan.popular && (
                    <div style={{
                      position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)',
                      background: plan.color, color: '#fff', borderRadius: 20,
                      padding: '4px 16px', fontSize: 12, fontWeight: 700,
                    }}>
                      MAIS POPULAR
                    </div>
                  )}
                  <h4 style={{ fontWeight: 700, color: plan.color, marginBottom: 4 }}>{plan.name}</h4>
                  <p style={{ color: '#888', fontSize: 13, marginBottom: 16 }}>{plan.description}</p>
                  <div style={{ marginBottom: 20 }}>
                    <span style={{ fontSize: 14, color: '#888' }}>R$</span>
                    <span style={{ fontSize: 48, fontWeight: 800, color: '#1a1a2e' }}>{plan.price}</span>
                    <span style={{ fontSize: 14, color: '#888' }}>/mes</span>
                  </div>
                  <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px', flex: 1 }}>
                    {plan.features.map((f, j) => (
                      <li key={j} style={{ padding: '6px 0', fontSize: 14, color: '#444', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <i className="fas fa-check-circle" style={{ color: plan.color, fontSize: 14 }} />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={onLogin}
                    style={{
                      background: plan.popular ? plan.color : 'transparent',
                      color: plan.popular ? '#fff' : plan.color,
                      border: `2px solid ${plan.color}`,
                      borderRadius: 12, padding: '12px 24px',
                      fontWeight: 700, fontSize: 15, cursor: 'pointer',
                      transition: 'all 0.2s', width: '100%',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = plan.color
                      e.currentTarget.style.color = '#fff'
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = plan.popular ? plan.color : 'transparent'
                      e.currentTarget.style.color = plan.popular ? '#fff' : plan.color
                    }}
                  >
                    {plan.cta}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section style={{
        padding: '80px 0',
        background: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
        color: '#fff', textAlign: 'center',
      }}>
        <div className="container" style={{ maxWidth: 600 }}>
          <h2 style={{ fontSize: 36, fontWeight: 800, marginBottom: 16 }}>
            Pronto para automatizar suas redes sociais?
          </h2>
          <p style={{ fontSize: 16, color: '#b8b8d4', marginBottom: 32, lineHeight: 1.7 }}>
            Junte-se a centenas de empresas que ja usam IA para criar conteudo
            profissional em minutos, nao em horas.
          </p>
          <button
            onClick={onLogin}
            style={{
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              color: '#fff', border: 'none', borderRadius: 12,
              padding: '16px 40px', fontWeight: 700, fontSize: 18, cursor: 'pointer',
              boxShadow: '0 8px 30px rgba(102,126,234,0.4)',
            }}
          >
            Comecar agora — 7 dias gratis <i className="fas fa-arrow-right ml-2" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: '40px 0', background: '#0a0a1a', color: '#666', fontSize: 13 }}>
        <div className="container d-flex justify-content-between align-items-center flex-wrap" style={{ gap: 16 }}>
          <div>
            <span style={{ fontWeight: 700, color: '#999' }}>Orbita<span style={{ color: '#6f42c1' }}>.IA</span></span>
            <span className="ml-3">Agencia de IA para redes sociais</span>
          </div>
          <div style={{ color: '#555' }}>
            {new Date().getFullYear()} Orbita.IA. Todos os direitos reservados.
          </div>
        </div>
      </footer>
    </div>
  )
}
