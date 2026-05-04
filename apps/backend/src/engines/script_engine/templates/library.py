"""
Template Library — Templates pré-prontos por nicho de negócio.
Cada template contém prompts otimizados, sugestões de paleta e hashtags.
"""
from typing import Any

TEMPLATES: list[dict[str, Any]] = [
    # ─── Saúde & Beleza ───
    {
        "id": "dentista-promocao",
        "nicho": "dentista",
        "nome": "Promocao de Tratamento",
        "descricao": "Post de promocao com desconto para tratamento odontologico",
        "formato": "post",
        "objective_template": "Promocao de {tratamento} com {desconto}% de desconto. Urgencia para agendar.",
        "tone": "profissional",
        "hashtags_sugeridas": ["odontologia", "sorriso", "clareamento", "dentista", "saude"],
        "paleta_sugerida": ["#00BCD4", "#FFFFFF", "#E0F7FA"],
        "visual_hint": "Close-up of bright smile, dental clinic modern interior, clean whites and teals",
    },
    {
        "id": "dentista-educativo",
        "nicho": "dentista",
        "nome": "Dica de Saude Bucal",
        "descricao": "Carrossel educativo com dicas de higiene ou tratamento",
        "formato": "carrossel",
        "objective_template": "5 dicas de {tema_saude_bucal} que todo mundo deveria saber",
        "tone": "educativo",
        "slide_count": 5,
        "hashtags_sugeridas": ["saudebucal", "dicasdedentista", "higienebucal", "odonto"],
        "paleta_sugerida": ["#1565C0", "#FFFFFF", "#BBDEFB"],
        "visual_hint": "Educational medical infographic style, clean modern design",
    },
    {
        "id": "estetica-antes-depois",
        "nicho": "clinica_estetica",
        "nome": "Antes e Depois",
        "descricao": "Post mostrando resultado de procedimento estetico",
        "formato": "carrossel",
        "objective_template": "Resultado incrivel de {procedimento}. Antes e depois real de paciente.",
        "tone": "profissional",
        "slide_count": 3,
        "hashtags_sugeridas": ["antesedepois", "estetica", "resultado", "beleza"],
        "paleta_sugerida": ["#E91E63", "#FCE4EC", "#FFFFFF"],
        "visual_hint": "Beauty clinic, soft feminine lighting, rose gold accents",
    },
    # ─── E-commerce ───
    {
        "id": "ecommerce-lancamento",
        "nicho": "ecommerce",
        "nome": "Lancamento de Produto",
        "descricao": "Post de lancamento com foto do produto e CTA de compra",
        "formato": "post",
        "objective_template": "Lancamento do novo {produto}. Disponivel agora com frete gratis.",
        "tone": "urgente",
        "hashtags_sugeridas": ["lancamento", "novidade", "compreagoralinknabio", "oferta"],
        "paleta_sugerida": ["#FF5722", "#FFF3E0", "#212121"],
        "visual_hint": "Product photography, dramatic lighting, luxury unboxing feel",
    },
    {
        "id": "ecommerce-promocao-relampago",
        "nicho": "ecommerce",
        "nome": "Promocao Relampago",
        "descricao": "Story com countdown de promocao limitada",
        "formato": "story",
        "objective_template": "FLASH SALE: {produto} com {desconto}% OFF. So hoje!",
        "tone": "urgente",
        "hashtags_sugeridas": ["promocao", "desconto", "flashsale", "corra"],
        "paleta_sugerida": ["#F44336", "#FFEB3B", "#000000"],
        "visual_hint": "Bold red and yellow, urgency feel, countdown timer aesthetic",
    },
    # ─── Restaurante ───
    {
        "id": "restaurante-prato-dia",
        "nicho": "restaurante",
        "nome": "Prato do Dia",
        "descricao": "Post com foto apetitosa do prato especial do dia",
        "formato": "post",
        "objective_template": "Prato do dia: {prato}. Feito com ingredientes frescos e muito amor.",
        "tone": "descontraido",
        "hashtags_sugeridas": ["gastronomia", "pratododia", "comidaboa", "restaurante", "foodporn"],
        "paleta_sugerida": ["#FF8F00", "#FFF8E1", "#3E2723"],
        "visual_hint": "Overhead flat lay food photography, warm golden lighting, rustic wooden table",
    },
    {
        "id": "restaurante-bastidores",
        "nicho": "restaurante",
        "nome": "Bastidores da Cozinha",
        "descricao": "Story mostrando o preparo dos pratos",
        "formato": "story",
        "objective_template": "Nos bastidores: como preparamos nosso famoso {prato}",
        "tone": "descontraido",
        "hashtags_sugeridas": ["bastidores", "cozinha", "chefdecozinha", "preparacao"],
        "paleta_sugerida": ["#FF6F00", "#FFFFFF", "#4E342E"],
        "visual_hint": "Kitchen action shot, steam rising, chef hands close-up, warm tones",
    },
    # ─── Imobiliária ───
    {
        "id": "imobiliaria-imovel",
        "nicho": "imobiliaria",
        "nome": "Imovel em Destaque",
        "descricao": "Carrossel com fotos do imovel e informacoes principais",
        "formato": "carrossel",
        "objective_template": "Imovel dos sonhos: {tipo_imovel} em {bairro}. {quartos} quartos, {area}m².",
        "tone": "profissional",
        "slide_count": 5,
        "hashtags_sugeridas": ["imovel", "apartamento", "casa", "imobiliaria", "vendadeimoveis"],
        "paleta_sugerida": ["#1A237E", "#E8EAF6", "#FFD600"],
        "visual_hint": "Real estate photography, wide angle, bright airy interiors, modern luxury",
    },
    # ─── Fitness ───
    {
        "id": "fitness-treino",
        "nicho": "fitness",
        "nome": "Dica de Treino",
        "descricao": "Post educativo com exercicio ou dica de treino",
        "formato": "post",
        "objective_template": "Exercicio {exercicio}: como fazer corretamente para {resultado}",
        "tone": "educativo",
        "hashtags_sugeridas": ["treino", "fitness", "academia", "saude", "exercicio"],
        "paleta_sugerida": ["#00C853", "#1B5E20", "#FFFFFF"],
        "visual_hint": "Athletic photography, dramatic gym lighting, high contrast, sweat detail",
    },
    {
        "id": "fitness-motivacional",
        "nicho": "fitness",
        "nome": "Motivacional",
        "descricao": "Story motivacional para engajar a comunidade",
        "formato": "story",
        "objective_template": "Frase motivacional sobre superacao e disciplina no treino",
        "tone": "descontraido",
        "hashtags_sugeridas": ["motivacao", "disciplina", "focoefenosol", "treinohard"],
        "paleta_sugerida": ["#FF6D00", "#000000", "#FFFFFF"],
        "visual_hint": "Silhouette athlete, sunrise/sunset, dramatic sky, inspirational mood",
    },
    # ─── Advocacia ───
    {
        "id": "advogado-informativo",
        "nicho": "advocacia",
        "nome": "Informativo Juridico",
        "descricao": "Carrossel educativo explicando direitos ou leis",
        "formato": "carrossel",
        "objective_template": "Voce sabia? {tema_juridico} — seus direitos explicados de forma simples",
        "tone": "educativo",
        "slide_count": 5,
        "hashtags_sugeridas": ["direito", "advogado", "leis", "justica", "informacaojuridica"],
        "paleta_sugerida": ["#37474F", "#CFD8DC", "#C6A052"],
        "visual_hint": "Legal office, leather bound books, scales of justice, warm dark tones",
    },
    # ─── Tecnologia / Consultoria IA ───
    {
        "id": "tech-consultoria-dor-solucao",
        "nicho": "tecnologia",
        "nome": "Dor → Solucao → CTA (Consultoria IA)",
        "descricao": "Carrossel de 5 slides: problema do cliente, dados impactantes, estrategia, liberdade, CTA consultoria",
        "formato": "carrossel",
        "objective_template": "Mostrar como automacao com IA resolve {dor_do_cliente} e oferecer consultoria gratuita",
        "tone": "urgente",
        "slide_count": 5,
        "hashtags_sugeridas": [
            "automacao", "inteligenciaartificial", "produtividade",
            "transformacaodigital", "gestao", "tecnologia", "ia",
            "consultoriagratuita", "orbitaia",
        ],
        "paleta_sugerida": ["#1a1a2e", "#0f3460", "#FF6B35", "#0a0e27", "#FFFFFF"],
        "visual_hint_slides": [
            # Slide 1 — Dor: 8h vs 8min
            (
                "Dramatic split-composition corporate scene. Left side: chaotic office desk drowning in "
                "paper stacks, tangled cables, multiple analog clocks showing 8 hours of wasted time, "
                "harsh cold fluorescent 5600K overhead lighting creating stress shadows. Right side: sleek "
                "minimalist desk with a single holographic dashboard floating mid-air, glowing vibrant orange "
                "(#FF6B35) data visualizations against deep cosmic black (#0a0e27). Cinematic split lighting — "
                "cold fluorescent left, warm orange rim light right. Shot on Sony A7R V, 24mm f/2.8, low angle. "
                "Color story: deep navy (#1a1a2e) shadows, dark blue (#0f3460) midtones, electric orange (#FF6B35) "
                "accents cutting through like a blade. No text overlays, no watermarks, no logos."
            ),
            # Slide 2 — Dado: 60% reducao de custos
            (
                "Futuristic data visualization floating in dark cosmic space (#0a0e27). Massive 3D holographic "
                "bar chart showing dramatic cost descent — bars descending from left to right, transitioning from "
                "red/stressed tones to cool blue (#0f3460) to vibrant orange (#FF6B35) at the lowest point. "
                "Particle effects and light trails connecting data points. Subtle grid lines in deep navy (#1a1a2e). "
                "Volumetric orange light rays emanating from the lowest bar. Background: stars and nebula-like "
                "abstract shapes. Shot with macro tilt-shift effect, f/1.4, extreme shallow depth of field on the "
                "key data point. No text, no watermarks, no logos."
            ),
            # Slide 3 — Insight: tecnologia + estrategia
            (
                "Conceptual still life: elegant chess pieces (king, queen) made of brushed dark metal (#1a1a2e) "
                "standing on a circuit board surface with glowing orange (#FF6B35) traces and pathways. The chess "
                "pieces cast long dramatic shadows. Background: deep blue (#0f3460) gradient fading to cosmic black "
                "(#0a0e27). A holographic brain/network diagram hovers faintly above the chess board, connecting "
                "strategy to technology. Rembrandt lighting from upper-left, warm 3200K key light with orange rim. "
                "Shot on 85mm f/1.4, shallow depth of field, product photography quality. Texture: matte metal, "
                "glossy circuit traces, subtle reflection on dark surface. No text, no watermarks, no logos."
            ),
            # Slide 4 — Promessa: liberdade
            (
                "Powerful silhouette of a confident business professional standing at floor-to-ceiling panoramic "
                "window, arms slightly open, gazing at a vast urban horizon at golden hour. The city skyline "
                "glows in deep blue (#0f3460) twilight with scattered orange (#FF6B35) lights. Interior is dark "
                "cosmic black (#0a0e27) creating dramatic contrast. Volumetric light rays streaming through the "
                "window in warm orange tones. The person's outline is rimlit with vibrant orange edge light. "
                "Feeling of freedom, power, and possibility. Shot on 35mm f/2.0, cinematic aspect ratio. "
                "Atmospheric haze adds depth layers. No text, no watermarks, no logos."
            ),
            # Slide 5 — CTA: consultoria gratuita
            (
                "Striking minimal composition: a luminous doorway/portal made of pure vibrant orange (#FF6B35) "
                "light standing in the middle of a vast dark cosmic space (#0a0e27). The portal emits warm light "
                "rays and particles that spread across the dark floor, creating reflections on a glossy surface. "
                "The surrounding space is deep navy (#1a1a2e) fading to cosmic black. A subtle path of orange "
                "light traces leads toward the portal, suggesting invitation. The portal frame has clean geometric "
                "edges. Volumetric fog adds atmosphere. Shot from eye level, 24mm wide angle, f/2.8. "
                "Mood: invitation, new beginning, opportunity. No text, no watermarks, no logos."
            ),
        ],
        "slide_texts_pt": [
            {
                "main": "Seu negócio gasta 8 HORAS\nem tarefas que IA faz em 8 MINUTOS?",
                "highlights": ["8 HORAS", "8 MINUTOS"],
            },
            {
                "main": "Automação com IA:\nredução de 60% nos custos\noperacionais",
                "highlights": ["60%"],
            },
            {
                "main": "Tecnologia sozinha não funciona.\nVocê precisa de ESTRATÉGIA.",
                "highlights": ["ESTRATÉGIA"],
            },
            {
                "main": "OrbitaIA não vende software.\nVende LIBERDADE.",
                "highlights": ["LIBERDADE"],
            },
            {
                "main": "Consultoria GRATUITA:\ndescubra onde você\nvaza dinheiro todo mês",
                "highlights": ["GRATUITA"],
            },
        ],
    },
]


def get_templates_for_nicho(nicho: str) -> list[dict]:
    """Retorna templates para um nicho específico."""
    nicho_lower = nicho.lower().strip()
    return [t for t in TEMPLATES if nicho_lower in t["nicho"].lower()]


def get_all_nichos() -> list[str]:
    """Retorna lista de nichos disponíveis."""
    return sorted(set(t["nicho"] for t in TEMPLATES))


def get_template_by_id(template_id: str) -> dict | None:
    """Retorna template por ID."""
    return next((t for t in TEMPLATES if t["id"] == template_id), None)


def suggest_templates(business_type: str) -> list[dict]:
    """Sugere templates baseado no tipo de negócio (fuzzy match)."""
    bt = business_type.lower()
    matches = []
    # Mapeamento de tipos comuns para nichos
    nicho_map = {
        "dentista": "dentista", "odontologia": "dentista", "clinica odontologica": "dentista",
        "estetica": "clinica_estetica", "clinica estetica": "clinica_estetica", "beleza": "clinica_estetica",
        "ecommerce": "ecommerce", "loja": "ecommerce", "loja virtual": "ecommerce", "e-commerce": "ecommerce",
        "restaurante": "restaurante", "pizzaria": "restaurante", "lanchonete": "restaurante", "bar": "restaurante",
        "imobiliaria": "imobiliaria", "corretor": "imobiliaria", "imoveis": "imobiliaria",
        "academia": "fitness", "fitness": "fitness", "personal": "fitness", "crossfit": "fitness",
        "advogado": "advocacia", "advocacia": "advocacia", "escritorio de advocacia": "advocacia",
        "tecnologia": "tecnologia", "tech": "tecnologia", "consultoria": "tecnologia",
        "automacao": "tecnologia", "ia": "tecnologia", "saas": "tecnologia", "software": "tecnologia",
    }
    for key, nicho in nicho_map.items():
        if key in bt:
            matches = get_templates_for_nicho(nicho)
            break
    # Fallback: retorna todos se não encontrou match
    if not matches:
        matches = TEMPLATES[:4]
    return matches
