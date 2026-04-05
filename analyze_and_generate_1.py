#!/usr/bin/env python3
"""
Profile Analyzer & Static Site Generator
=========================================
Sistema para análise de banco de dados de mídia (imagens, prints, fontes)
e geração de site estático profissional.

Estrutura esperada do banco de dados:
database/
├── profile/
│   ├── photos/          # Fotos de perfil, profissionais
│   ├── instagram/       # Prints do Instagram
│   └── logo/            # Logos e marca
├── portfolio/
│   ├── projects/        # Fotos de projetos
│   └── certificates/    # Certificados, diplomas
├── media/
│   ├── videos/          # Vídeos curtos
│   └── docs/            # PDFs, documentos
└── config/
    ├── profile.json     # Dados do profissional
    ├── colors.json      # Paleta de cores extraída
    └── fonts/           # Fontes customizadas
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
import base64
import re

# ============================================================================
# MODELOS DE DADOS
# ============================================================================

@dataclass
class ProfileData:
    """Dados do profissional"""
    name: str = ""
    title: str = ""
    tagline: str = ""
    bio: str = ""
    email: str = ""
    phone: str = ""
    whatsapp: str = ""
    instagram: str = ""
    linkedin: str = ""
    location: str = ""
    logo_path: str = ""
    profile_photo: str = ""
    
@dataclass
class ColorPalette:
    """Paleta de cores do site"""
    primary: str = "#1a1a2e"
    secondary: str = "#16213e"
    accent: str = "#e94560"
    text: str = "#eaeaea"
    text_muted: str = "#a0a0a0"
    background: str = "#0f0f1a"
    surface: str = "#1a1a2e"
    
@dataclass
class ProjectItem:
    """Item de portfólio"""
    id: str = ""
    title: str = ""
    description: str = ""
    category: str = ""
    images: list = None
    date: str = ""
    
    def __post_init__(self):
        if self.images is None:
            self.images = []

@dataclass
class AnalysisResult:
    """Resultado da análise completa"""
    profile: ProfileData = None
    colors: ColorPalette = None
    projects: list = None
    instagram_posts: list = None
    certificates: list = None
    fonts: list = None
    generated_at: str = ""
    
    def __post_init__(self):
        if self.profile is None:
            self.profile = ProfileData()
        if self.colors is None:
            self.colors = ColorPalette()
        if self.projects is None:
            self.projects = []
        if self.instagram_posts is None:
            self.instagram_posts = []
        if self.certificates is None:
            self.certificates = []
        if self.fonts is None:
            self.fonts = []


# ============================================================================
# ANALISADOR DE MÍDIA
# ============================================================================

class MediaAnalyzer:
    """Analisa o banco de dados de mídia"""
    
    SUPPORTED_IMAGES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    SUPPORTED_VIDEOS = {'.mp4', '.webm', '.mov'}
    SUPPORTED_DOCS = {'.pdf'}
    SUPPORTED_FONTS = {'.ttf', '.otf', '.woff', '.woff2'}
    
    def __init__(self, database_path: str):
        self.db_path = Path(database_path)
        self.result = AnalysisResult()
        
    def analyze(self) -> AnalysisResult:
        """Executa análise completa do banco de dados"""
        print("🔍 Iniciando análise do banco de dados...")
        
        self._load_profile_config()
        self._load_color_config()
        self._scan_profile_photos()
        self._scan_instagram()
        self._scan_portfolio()
        self._scan_certificates()
        self._scan_fonts()
        
        self.result.generated_at = datetime.now().isoformat()
        
        print("✅ Análise concluída!")
        return self.result
    
    def _load_profile_config(self):
        """Carrega configuração de perfil"""
        config_file = self.db_path / "config" / "profile.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.result.profile = ProfileData(**data)
            print(f"  📋 Perfil carregado: {self.result.profile.name}")
        else:
            print("  ⚠️  Arquivo profile.json não encontrado")
            
    def _load_color_config(self):
        """Carrega paleta de cores"""
        config_file = self.db_path / "config" / "colors.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.result.colors = ColorPalette(**data)
            print(f"  🎨 Paleta carregada: {self.result.colors.primary}")
        else:
            print("  ⚠️  Usando paleta padrão")
            
    def _scan_profile_photos(self):
        """Escaneia fotos de perfil"""
        photos_dir = self.db_path / "profile" / "photos"
        logo_dir = self.db_path / "profile" / "logo"
        
        if photos_dir.exists():
            photos = list(self._get_images(photos_dir))
            if photos:
                self.result.profile.profile_photo = str(photos[0])
                print(f"  📸 Foto de perfil: {photos[0].name}")
                
        if logo_dir.exists():
            logos = list(self._get_images(logo_dir))
            if logos:
                self.result.profile.logo_path = str(logos[0])
                print(f"  🏷️  Logo: {logos[0].name}")
                
    def _scan_instagram(self):
        """Escaneia prints do Instagram"""
        insta_dir = self.db_path / "profile" / "instagram"
        if insta_dir.exists():
            posts = []
            for img in self._get_images(insta_dir):
                posts.append({
                    'path': str(img),
                    'filename': img.name,
                    'date': datetime.fromtimestamp(img.stat().st_mtime).isoformat()
                })
            self.result.instagram_posts = sorted(posts, key=lambda x: x['date'], reverse=True)
            print(f"  📱 Instagram: {len(posts)} posts encontrados")
            
    def _scan_portfolio(self):
        """Escaneia projetos do portfólio"""
        projects_dir = self.db_path / "portfolio" / "projects"
        if projects_dir.exists():
            projects = []
            # Cada subpasta é um projeto
            for project_folder in projects_dir.iterdir():
                if project_folder.is_dir():
                    images = list(self._get_images(project_folder))
                    
                    # Tenta carregar metadata
                    meta_file = project_folder / "meta.json"
                    if meta_file.exists():
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                    else:
                        meta = {
                            'title': project_folder.name.replace('_', ' ').title(),
                            'description': '',
                            'category': 'Geral'
                        }
                    
                    project = ProjectItem(
                        id=project_folder.name,
                        title=meta.get('title', project_folder.name),
                        description=meta.get('description', ''),
                        category=meta.get('category', 'Geral'),
                        images=[str(img) for img in images],
                        date=meta.get('date', '')
                    )
                    projects.append(asdict(project))
                    
            self.result.projects = projects
            print(f"  🏗️  Projetos: {len(projects)} encontrados")
            
    def _scan_certificates(self):
        """Escaneia certificados"""
        certs_dir = self.db_path / "portfolio" / "certificates"
        if certs_dir.exists():
            certs = []
            for cert in certs_dir.iterdir():
                if cert.suffix.lower() in self.SUPPORTED_IMAGES | self.SUPPORTED_DOCS:
                    certs.append({
                        'path': str(cert),
                        'filename': cert.name,
                        'type': 'image' if cert.suffix.lower() in self.SUPPORTED_IMAGES else 'pdf'
                    })
            self.result.certificates = certs
            print(f"  📜 Certificados: {len(certs)} encontrados")
            
    def _scan_fonts(self):
        """Escaneia fontes customizadas"""
        fonts_dir = self.db_path / "config" / "fonts"
        if fonts_dir.exists():
            fonts = []
            for font in fonts_dir.iterdir():
                if font.suffix.lower() in self.SUPPORTED_FONTS:
                    fonts.append({
                        'path': str(font),
                        'filename': font.name,
                        'family': font.stem.replace('-', ' ').replace('_', ' ')
                    })
            self.result.fonts = fonts
            print(f"  🔤 Fontes: {len(fonts)} encontradas")
            
    def _get_images(self, directory: Path):
        """Generator para imagens em um diretório"""
        for file in directory.iterdir():
            if file.suffix.lower() in self.SUPPORTED_IMAGES:
                yield file


# ============================================================================
# GERADOR DE SITE
# ============================================================================

class SiteGenerator:
    """Gera site estático a partir dos dados analisados"""
    
    def __init__(self, analysis: AnalysisResult, output_path: str):
        self.data = analysis
        self.output = Path(output_path)
        self.assets_dir = self.output / "assets"
        
    def generate(self):
        """Gera o site completo"""
        print("\n🚀 Gerando site estático...")
        
        self._prepare_directories()
        self._copy_assets()
        self._generate_css()
        self._generate_js()
        self._generate_html()
        self._generate_data_json()
        
        print(f"✅ Site gerado em: {self.output}")
        
    def _prepare_directories(self):
        """Cria estrutura de diretórios"""
        dirs = [
            self.output,
            self.assets_dir / "css",
            self.assets_dir / "js",
            self.assets_dir / "images" / "profile",
            self.assets_dir / "images" / "portfolio",
            self.assets_dir / "images" / "instagram",
            self.assets_dir / "fonts",
            self.output / "data",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        print("  📁 Diretórios criados")
        
    def _copy_assets(self):
        """Copia assets para o site"""
        # Copia foto de perfil
        if self.data.profile.profile_photo:
            src = Path(self.data.profile.profile_photo)
            if src.exists():
                dst = self.assets_dir / "images" / "profile" / src.name
                shutil.copy2(src, dst)
                self.data.profile.profile_photo = f"assets/images/profile/{src.name}"
                
        # Copia logo
        if self.data.profile.logo_path:
            src = Path(self.data.profile.logo_path)
            if src.exists():
                dst = self.assets_dir / "images" / "profile" / src.name
                shutil.copy2(src, dst)
                self.data.profile.logo_path = f"assets/images/profile/{src.name}"
                
        # Copia imagens de projetos
        for project in self.data.projects:
            new_images = []
            for img_path in project['images']:
                src = Path(img_path)
                if src.exists():
                    dst = self.assets_dir / "images" / "portfolio" / src.name
                    shutil.copy2(src, dst)
                    new_images.append(f"assets/images/portfolio/{src.name}")
            project['images'] = new_images
            
        # Copia posts do Instagram
        for post in self.data.instagram_posts:
            src = Path(post['path'])
            if src.exists():
                dst = self.assets_dir / "images" / "instagram" / src.name
                shutil.copy2(src, dst)
                post['path'] = f"assets/images/instagram/{src.name}"
                
        # Copia fontes
        for font in self.data.fonts:
            src = Path(font['path'])
            if src.exists():
                dst = self.assets_dir / "fonts" / src.name
                shutil.copy2(src, dst)
                font['path'] = f"assets/fonts/{src.name}"
                
        print("  📦 Assets copiados")
        
    def _generate_css(self):
        """Gera arquivo CSS principal"""
        colors = self.data.colors
        
        # Font-face para fontes customizadas
        font_faces = ""
        for font in self.data.fonts:
            ext = Path(font['filename']).suffix.lower()
            fmt = {'.ttf': 'truetype', '.otf': 'opentype', '.woff': 'woff', '.woff2': 'woff2'}.get(ext, 'truetype')
            font_faces += f"""
@font-face {{
    font-family: '{font['family']}';
    src: url('../{font['path']}') format('{fmt}');
    font-display: swap;
}}
"""
        
        css = f'''/* 
 * Site Profissional - Gerado automaticamente
 * {datetime.now().strftime('%Y-%m-%d %H:%M')}
 */

{font_faces}

:root {{
    --color-primary: {colors.primary};
    --color-secondary: {colors.secondary};
    --color-accent: {colors.accent};
    --color-text: {colors.text};
    --color-text-muted: {colors.text_muted};
    --color-background: {colors.background};
    --color-surface: {colors.surface};
    
    --font-display: 'Clash Display', 'SF Pro Display', system-ui, sans-serif;
    --font-body: 'Satoshi', 'SF Pro Text', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 2rem;
    --space-xl: 4rem;
    --space-2xl: 8rem;
    
    --radius-sm: 0.375rem;
    --radius-md: 0.75rem;
    --radius-lg: 1.5rem;
    --radius-full: 9999px;
    
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
    --shadow-glow: 0 0 40px rgba(233, 69, 96, 0.3);
    
    --transition-fast: 150ms ease;
    --transition-base: 300ms ease;
    --transition-slow: 500ms ease;
}}

/* Reset & Base */
*, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

html {{
    scroll-behavior: smooth;
    font-size: 16px;
}}

body {{
    font-family: var(--font-body);
    background: var(--color-background);
    color: var(--color-text);
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
}}

/* Background Pattern */
body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background: 
        radial-gradient(circle at 20% 50%, rgba(233, 69, 96, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(22, 33, 62, 0.5) 0%, transparent 40%),
        radial-gradient(circle at 40% 80%, rgba(233, 69, 96, 0.05) 0%, transparent 40%);
    pointer-events: none;
    z-index: -1;
}}

/* Typography */
h1, h2, h3, h4 {{
    font-family: var(--font-display);
    font-weight: 600;
    line-height: 1.2;
    letter-spacing: -0.02em;
}}

h1 {{ font-size: clamp(2.5rem, 8vw, 4.5rem); }}
h2 {{ font-size: clamp(1.75rem, 5vw, 2.5rem); }}
h3 {{ font-size: clamp(1.25rem, 3vw, 1.5rem); }}

a {{
    color: var(--color-accent);
    text-decoration: none;
    transition: color var(--transition-fast);
}}

a:hover {{
    color: var(--color-text);
}}

/* Container */
.container {{
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--space-lg);
}}

/* Header */
.header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    padding: var(--space-md) 0;
    background: rgba(15, 15, 26, 0.8);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: all var(--transition-base);
}}

.header.scrolled {{
    padding: var(--space-sm) 0;
    background: rgba(15, 15, 26, 0.95);
}}

.header__inner {{
    display: flex;
    align-items: center;
    justify-content: space-between;
}}

.header__logo {{
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--color-text);
}}

.header__logo img {{
    height: 40px;
    width: auto;
}}

.nav {{
    display: flex;
    gap: var(--space-lg);
}}

.nav__link {{
    color: var(--color-text-muted);
    font-size: 0.9rem;
    font-weight: 500;
    position: relative;
    padding: var(--space-xs) 0;
}}

.nav__link::after {{
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 0;
    height: 2px;
    background: var(--color-accent);
    transition: width var(--transition-base);
}}

.nav__link:hover,
.nav__link.active {{
    color: var(--color-text);
}}

.nav__link:hover::after,
.nav__link.active::after {{
    width: 100%;
}}

/* Mobile Menu */
.menu-toggle {{
    display: none;
    flex-direction: column;
    gap: 5px;
    background: none;
    border: none;
    cursor: pointer;
    padding: var(--space-sm);
}}

.menu-toggle span {{
    width: 24px;
    height: 2px;
    background: var(--color-text);
    transition: var(--transition-fast);
}}

/* Hero Section */
.hero {{
    min-height: 100vh;
    display: flex;
    align-items: center;
    padding: var(--space-2xl) 0;
    position: relative;
}}

.hero__content {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-xl);
    align-items: center;
}}

.hero__text {{
    animation: fadeInUp 0.8s ease forwards;
}}

.hero__badge {{
    display: inline-flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-xs) var(--space-md);
    background: rgba(233, 69, 96, 0.1);
    border: 1px solid rgba(233, 69, 96, 0.3);
    border-radius: var(--radius-full);
    font-size: 0.85rem;
    color: var(--color-accent);
    margin-bottom: var(--space-lg);
}}

.hero__badge::before {{
    content: '';
    width: 8px;
    height: 8px;
    background: var(--color-accent);
    border-radius: 50%;
    animation: pulse 2s infinite;
}}

.hero__title {{
    margin-bottom: var(--space-md);
}}

.hero__title span {{
    color: var(--color-accent);
}}

.hero__subtitle {{
    font-size: 1.25rem;
    color: var(--color-text-muted);
    margin-bottom: var(--space-lg);
    max-width: 500px;
}}

.hero__actions {{
    display: flex;
    gap: var(--space-md);
    flex-wrap: wrap;
}}

.hero__image {{
    position: relative;
    animation: fadeInUp 0.8s 0.2s ease forwards;
    opacity: 0;
}}

.hero__image img {{
    width: 100%;
    max-width: 450px;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    margin-left: auto;
    display: block;
}}

.hero__image::before {{
    content: '';
    position: absolute;
    inset: -20px;
    background: linear-gradient(135deg, var(--color-accent), transparent);
    border-radius: var(--radius-lg);
    opacity: 0.2;
    z-index: -1;
    transform: rotate(3deg);
}}

/* Buttons */
.btn {{
    display: inline-flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-md) var(--space-lg);
    font-family: var(--font-body);
    font-size: 0.95rem;
    font-weight: 600;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-base);
    border: none;
    text-decoration: none;
}}

.btn--primary {{
    background: var(--color-accent);
    color: white;
}}

.btn--primary:hover {{
    background: #ff6b81;
    transform: translateY(-2px);
    box-shadow: var(--shadow-glow);
}}

.btn--secondary {{
    background: transparent;
    color: var(--color-text);
    border: 1px solid rgba(255,255,255,0.2);
}}

.btn--secondary:hover {{
    border-color: var(--color-accent);
    color: var(--color-accent);
}}

/* Sections */
.section {{
    padding: var(--space-2xl) 0;
}}

.section__header {{
    text-align: center;
    margin-bottom: var(--space-xl);
}}

.section__label {{
    display: inline-block;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--color-accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--space-sm);
}}

.section__title {{
    margin-bottom: var(--space-md);
}}

.section__description {{
    color: var(--color-text-muted);
    max-width: 600px;
    margin: 0 auto;
}}

/* About Section */
.about__content {{
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: var(--space-xl);
    align-items: start;
}}

.about__image img {{
    width: 100%;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
}}

.about__text p {{
    margin-bottom: var(--space-md);
    color: var(--color-text-muted);
}}

.about__stats {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-lg);
    margin-top: var(--space-xl);
    padding-top: var(--space-xl);
    border-top: 1px solid rgba(255,255,255,0.1);
}}

.stat {{
    text-align: center;
}}

.stat__number {{
    font-family: var(--font-display);
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--color-accent);
    line-height: 1;
}}

.stat__label {{
    font-size: 0.9rem;
    color: var(--color-text-muted);
    margin-top: var(--space-xs);
}}

/* Portfolio Grid */
.portfolio__grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: var(--space-lg);
}}

.project-card {{
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
    transition: all var(--transition-base);
}}

.project-card:hover {{
    transform: translateY(-8px);
    box-shadow: var(--shadow-lg);
    border-color: rgba(233, 69, 96, 0.3);
}}

.project-card__image {{
    aspect-ratio: 16/10;
    overflow: hidden;
}}

.project-card__image img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform var(--transition-slow);
}}

.project-card:hover .project-card__image img {{
    transform: scale(1.05);
}}

.project-card__content {{
    padding: var(--space-lg);
}}

.project-card__category {{
    font-size: 0.8rem;
    color: var(--color-accent);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: var(--space-sm);
}}

.project-card__title {{
    margin-bottom: var(--space-sm);
}}

.project-card__description {{
    color: var(--color-text-muted);
    font-size: 0.9rem;
}}

/* Contact Section */
.contact__content {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-xl);
}}

.contact__info {{
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
}}

.contact__item {{
    display: flex;
    align-items: flex-start;
    gap: var(--space-md);
}}

.contact__icon {{
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(233, 69, 96, 0.1);
    border-radius: var(--radius-md);
    color: var(--color-accent);
    font-size: 1.25rem;
    flex-shrink: 0;
}}

.contact__label {{
    font-size: 0.85rem;
    color: var(--color-text-muted);
    margin-bottom: var(--space-xs);
}}

.contact__value {{
    font-size: 1.1rem;
    font-weight: 500;
}}

.contact__form {{
    background: var(--color-surface);
    padding: var(--space-xl);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(255,255,255,0.05);
}}

.form-group {{
    margin-bottom: var(--space-md);
}}

.form-group label {{
    display: block;
    font-size: 0.9rem;
    color: var(--color-text-muted);
    margin-bottom: var(--space-sm);
}}

.form-group input,
.form-group textarea {{
    width: 100%;
    padding: var(--space-md);
    background: var(--color-background);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: var(--radius-md);
    color: var(--color-text);
    font-family: var(--font-body);
    font-size: 1rem;
    transition: border-color var(--transition-fast);
}}

.form-group input:focus,
.form-group textarea:focus {{
    outline: none;
    border-color: var(--color-accent);
}}

.form-group textarea {{
    min-height: 120px;
    resize: vertical;
}}

/* Footer */
.footer {{
    padding: var(--space-xl) 0;
    border-top: 1px solid rgba(255,255,255,0.05);
    text-align: center;
}}

.footer__social {{
    display: flex;
    justify-content: center;
    gap: var(--space-md);
    margin-bottom: var(--space-lg);
}}

.footer__social a {{
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    border-radius: var(--radius-full);
    color: var(--color-text-muted);
    transition: all var(--transition-fast);
}}

.footer__social a:hover {{
    background: var(--color-accent);
    color: white;
    transform: translateY(-3px);
}}

.footer__copy {{
    color: var(--color-text-muted);
    font-size: 0.9rem;
}}

/* Animations */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(30px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
}}

/* Responsive */
@media (max-width: 968px) {{
    .hero__content {{
        grid-template-columns: 1fr;
        text-align: center;
    }}
    
    .hero__subtitle {{
        margin-left: auto;
        margin-right: auto;
    }}
    
    .hero__actions {{
        justify-content: center;
    }}
    
    .hero__image {{
        order: -1;
    }}
    
    .hero__image img {{
        max-width: 300px;
        margin: 0 auto;
    }}
    
    .about__content {{
        grid-template-columns: 1fr;
    }}
    
    .contact__content {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 768px) {{
    .nav {{
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--color-surface);
        flex-direction: column;
        padding: var(--space-lg);
        gap: var(--space-md);
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    
    .nav.active {{
        display: flex;
    }}
    
    .menu-toggle {{
        display: flex;
    }}
    
    .about__stats {{
        grid-template-columns: 1fr;
        gap: var(--space-md);
    }}
    
    .portfolio__grid {{
        grid-template-columns: 1fr;
    }}
}}

/* Utility Classes */
.text-accent {{ color: var(--color-accent); }}
.text-muted {{ color: var(--color-text-muted); }}
.mt-sm {{ margin-top: var(--space-sm); }}
.mt-md {{ margin-top: var(--space-md); }}
.mt-lg {{ margin-top: var(--space-lg); }}
.mb-sm {{ margin-bottom: var(--space-sm); }}
.mb-md {{ margin-bottom: var(--space-md); }}
.mb-lg {{ margin-bottom: var(--space-lg); }}
'''
        
        css_file = self.assets_dir / "css" / "style.css"
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css)
        print("  🎨 CSS gerado")
        
    def _generate_js(self):
        """Gera arquivo JavaScript principal"""
        js = '''/**
 * Site Profissional - JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initHeader();
    initMobileMenu();
    initSmoothScroll();
    initAnimations();
    initContactForm();
});

// Header scroll effect
function initHeader() {
    const header = document.querySelector('.header');
    if (!header) return;
    
    const handleScroll = () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
}

// Mobile menu toggle
function initMobileMenu() {
    const toggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('.nav');
    
    if (!toggle || !nav) return;
    
    toggle.addEventListener('click', () => {
        nav.classList.toggle('active');
        toggle.classList.toggle('active');
    });
    
    // Close menu when clicking a link
    nav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            nav.classList.remove('active');
            toggle.classList.remove('active');
        });
    });
}

// Smooth scroll for anchor links
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Scroll-based animations
function initAnimations() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );
    
    document.querySelectorAll('.project-card, .section__header, .about__content, .contact__content').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Add the animation class styles
    const style = document.createElement('style');
    style.textContent = '.animate-in { opacity: 1 !important; transform: translateY(0) !important; }';
    document.head.appendChild(style);
}

// Contact form handling
function initContactForm() {
    const form = document.querySelector('.contact__form form');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        // Generate WhatsApp message
        const phone = document.querySelector('[data-whatsapp]')?.dataset.whatsapp || '';
        if (phone) {
            const message = encodeURIComponent(
                `Olá! Vim pelo site.\\n\\n` +
                `*Nome:* ${data.name}\\n` +
                `*Email:* ${data.email}\\n` +
                `*Mensagem:* ${data.message}`
            );
            window.open(`https://wa.me/${phone}?text=${message}`, '_blank');
        }
        
        // Show success message
        const btn = form.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        btn.textContent = 'Mensagem enviada! ✓';
        btn.disabled = true;
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
            form.reset();
        }, 3000);
    });
}

// Utility: Load data from JSON
async function loadSiteData() {
    try {
        const response = await fetch('/data/site-data.json');
        return await response.json();
    } catch (error) {
        console.error('Error loading site data:', error);
        return null;
    }
}
'''
        
        js_file = self.assets_dir / "js" / "main.js"
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js)
        print("  ⚡ JavaScript gerado")
        
    def _generate_html(self):
        """Gera arquivo HTML principal"""
        p = self.data.profile
        
        # Prepare portfolio HTML
        portfolio_html = ""
        for project in self.data.projects:
            img = project['images'][0] if project['images'] else ''
            portfolio_html += f'''
            <article class="project-card">
                <div class="project-card__image">
                    <img src="{img}" alt="{project['title']}" loading="lazy">
                </div>
                <div class="project-card__content">
                    <span class="project-card__category">{project['category']}</span>
                    <h3 class="project-card__title">{project['title']}</h3>
                    <p class="project-card__description">{project['description']}</p>
                </div>
            </article>
'''
        
        # Prepare WhatsApp number (digits only)
        whatsapp_number = re.sub(r'\D', '', p.whatsapp) if p.whatsapp else ''
        
        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{p.tagline}">
    <meta name="author" content="{p.name}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{p.name} - {p.title}">
    <meta property="og:description" content="{p.tagline}">
    <meta property="og:type" content="website">
    
    <title>{p.name} | {p.title}</title>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    
    <!-- Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Styles -->
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="container">
            <div class="header__inner">
                <a href="#" class="header__logo">
                    {f'<img src="{p.logo_path}" alt="{p.name}">' if p.logo_path else f'<span>{p.name}</span>'}
                </a>
                
                <nav class="nav">
                    <a href="#inicio" class="nav__link active">Início</a>
                    <a href="#sobre" class="nav__link">Sobre</a>
                    <a href="#portfolio" class="nav__link">Portfólio</a>
                    <a href="#contato" class="nav__link">Contato</a>
                </nav>
                
                <button class="menu-toggle" aria-label="Menu">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </div>
    </header>
    
    <!-- Hero Section -->
    <section id="inicio" class="hero">
        <div class="container">
            <div class="hero__content">
                <div class="hero__text">
                    <span class="hero__badge">Disponível para projetos</span>
                    <h1 class="hero__title">
                        {p.name.split()[0] if p.name else 'Olá'}, <span>{p.title}</span>
                    </h1>
                    <p class="hero__subtitle">{p.tagline}</p>
                    <div class="hero__actions">
                        <a href="#contato" class="btn btn--primary">
                            <i class="fab fa-whatsapp"></i>
                            Fale Comigo
                        </a>
                        <a href="#portfolio" class="btn btn--secondary">
                            Ver Projetos
                        </a>
                    </div>
                </div>
                <div class="hero__image">
                    {f'<img src="{p.profile_photo}" alt="{p.name}">' if p.profile_photo else ''}
                </div>
            </div>
        </div>
    </section>
    
    <!-- About Section -->
    <section id="sobre" class="section">
        <div class="container">
            <div class="section__header">
                <span class="section__label">Sobre Mim</span>
                <h2 class="section__title">Conheça meu trabalho</h2>
            </div>
            
            <div class="about__content">
                <div class="about__image">
                    {f'<img src="{p.profile_photo}" alt="{p.name}">' if p.profile_photo else ''}
                </div>
                <div class="about__text">
                    <p>{p.bio}</p>
                    
                    <div class="about__stats">
                        <div class="stat">
                            <span class="stat__number" data-count="5">5+</span>
                            <span class="stat__label">Anos de experiência</span>
                        </div>
                        <div class="stat">
                            <span class="stat__number" data-count="100">100+</span>
                            <span class="stat__label">Projetos realizados</span>
                        </div>
                        <div class="stat">
                            <span class="stat__number" data-count="50">50+</span>
                            <span class="stat__label">Clientes satisfeitos</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- Portfolio Section -->
    <section id="portfolio" class="section">
        <div class="container">
            <div class="section__header">
                <span class="section__label">Portfólio</span>
                <h2 class="section__title">Projetos Recentes</h2>
                <p class="section__description">
                    Confira alguns dos trabalhos que realizei recentemente.
                </p>
            </div>
            
            <div class="portfolio__grid">
                {portfolio_html if portfolio_html else '''
                <article class="project-card">
                    <div class="project-card__content">
                        <p class="project-card__description">
                            Adicione projetos na pasta portfolio/projects do banco de dados.
                        </p>
                    </div>
                </article>
                '''}
            </div>
        </div>
    </section>
    
    <!-- Contact Section -->
    <section id="contato" class="section">
        <div class="container">
            <div class="section__header">
                <span class="section__label">Contato</span>
                <h2 class="section__title">Vamos conversar?</h2>
                <p class="section__description">
                    Entre em contato para discutir seu próximo projeto.
                </p>
            </div>
            
            <div class="contact__content">
                <div class="contact__info">
                    {f'''
                    <div class="contact__item" data-whatsapp="{whatsapp_number}">
                        <div class="contact__icon">
                            <i class="fab fa-whatsapp"></i>
                        </div>
                        <div>
                            <span class="contact__label">WhatsApp</span>
                            <a href="https://wa.me/{whatsapp_number}" class="contact__value">{p.whatsapp}</a>
                        </div>
                    </div>
                    ''' if p.whatsapp else ''}
                    
                    {f'''
                    <div class="contact__item">
                        <div class="contact__icon">
                            <i class="fas fa-envelope"></i>
                        </div>
                        <div>
                            <span class="contact__label">E-mail</span>
                            <a href="mailto:{p.email}" class="contact__value">{p.email}</a>
                        </div>
                    </div>
                    ''' if p.email else ''}
                    
                    {f'''
                    <div class="contact__item">
                        <div class="contact__icon">
                            <i class="fab fa-instagram"></i>
                        </div>
                        <div>
                            <span class="contact__label">Instagram</span>
                            <a href="https://instagram.com/{p.instagram.replace('@', '')}" target="_blank" class="contact__value">{p.instagram}</a>
                        </div>
                    </div>
                    ''' if p.instagram else ''}
                    
                    {f'''
                    <div class="contact__item">
                        <div class="contact__icon">
                            <i class="fas fa-map-marker-alt"></i>
                        </div>
                        <div>
                            <span class="contact__label">Localização</span>
                            <span class="contact__value">{p.location}</span>
                        </div>
                    </div>
                    ''' if p.location else ''}
                </div>
                
                <div class="contact__form">
                    <form>
                        <div class="form-group">
                            <label for="name">Nome</label>
                            <input type="text" id="name" name="name" required placeholder="Seu nome">
                        </div>
                        <div class="form-group">
                            <label for="email">E-mail</label>
                            <input type="email" id="email" name="email" required placeholder="seu@email.com">
                        </div>
                        <div class="form-group">
                            <label for="message">Mensagem</label>
                            <textarea id="message" name="message" required placeholder="Como posso ajudar?"></textarea>
                        </div>
                        <button type="submit" class="btn btn--primary" style="width: 100%;">
                            <i class="fas fa-paper-plane"></i>
                            Enviar Mensagem
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </section>
    
    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer__social">
                {f'<a href="https://instagram.com/{p.instagram.replace("@", "")}" target="_blank" aria-label="Instagram"><i class="fab fa-instagram"></i></a>' if p.instagram else ''}
                {f'<a href="https://linkedin.com/in/{p.linkedin}" target="_blank" aria-label="LinkedIn"><i class="fab fa-linkedin-in"></i></a>' if p.linkedin else ''}
                {f'<a href="https://wa.me/{whatsapp_number}" target="_blank" aria-label="WhatsApp"><i class="fab fa-whatsapp"></i></a>' if p.whatsapp else ''}
                {f'<a href="mailto:{p.email}" aria-label="E-mail"><i class="fas fa-envelope"></i></a>' if p.email else ''}
            </div>
            <p class="footer__copy">
                &copy; {datetime.now().year} {p.name}. Todos os direitos reservados.
            </p>
        </div>
    </footer>
    
    <!-- Scripts -->
    <script src="assets/js/main.js"></script>
</body>
</html>
'''
        
        html_file = self.output / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print("  📄 HTML gerado")
        
    def _generate_data_json(self):
        """Gera JSON com dados do site para uso dinâmico"""
        data = {
            'profile': asdict(self.data.profile),
            'colors': asdict(self.data.colors),
            'projects': self.data.projects,
            'instagram_posts': self.data.instagram_posts,
            'certificates': self.data.certificates,
            'generated_at': self.data.generated_at
        }
        
        json_file = self.output / "data" / "site-data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("  📊 JSON de dados gerado")


# ============================================================================
# CRIADOR DE ESTRUTURA DE BANCO DE DADOS
# ============================================================================

def create_database_structure(base_path: str):
    """Cria estrutura inicial do banco de dados com arquivos de exemplo"""
    base = Path(base_path)
    
    # Estrutura de diretórios
    dirs = [
        "profile/photos",
        "profile/instagram",
        "profile/logo",
        "portfolio/projects/projeto_exemplo",
        "portfolio/certificates",
        "media/videos",
        "media/docs",
        "config/fonts",
    ]
    
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    
    # Arquivo de perfil exemplo
    profile_example = {
        "name": "Seu Nome",
        "title": "Sua Profissão",
        "tagline": "Uma breve descrição do que você faz",
        "bio": "Conte sua história aqui. Fale sobre sua experiência, especializações e o que te diferencia no mercado. Este texto aparecerá na seção 'Sobre' do site.",
        "email": "contato@seusite.com",
        "phone": "(00) 00000-0000",
        "whatsapp": "5500000000000",
        "instagram": "@seuinstagram",
        "linkedin": "seu-perfil",
        "location": "Sua Cidade, Estado"
    }
    
    with open(base / "config" / "profile.json", 'w', encoding='utf-8') as f:
        json.dump(profile_example, f, ensure_ascii=False, indent=2)
    
    # Arquivo de cores exemplo
    colors_example = {
        "primary": "#1a1a2e",
        "secondary": "#16213e",
        "accent": "#e94560",
        "text": "#eaeaea",
        "text_muted": "#a0a0a0",
        "background": "#0f0f1a",
        "surface": "#1a1a2e"
    }
    
    with open(base / "config" / "colors.json", 'w', encoding='utf-8') as f:
        json.dump(colors_example, f, ensure_ascii=False, indent=2)
    
    # Metadata de projeto exemplo
    project_meta = {
        "title": "Nome do Projeto",
        "description": "Descrição breve do projeto realizado",
        "category": "Categoria",
        "date": "2024-01"
    }
    
    with open(base / "portfolio" / "projects" / "projeto_exemplo" / "meta.json", 'w', encoding='utf-8') as f:
        json.dump(project_meta, f, ensure_ascii=False, indent=2)
    
    # README com instruções
    readme = """# Banco de Dados de Mídia

## Estrutura

```
database/
├── profile/
│   ├── photos/          # Suas fotos de perfil (a primeira será usada)
│   ├── instagram/       # Prints do Instagram
│   └── logo/            # Logo da empresa/marca
├── portfolio/
│   ├── projects/        # Cada subpasta é um projeto
│   │   └── nome_projeto/
│   │       ├── meta.json    # Metadados do projeto
│   │       └── *.jpg/png    # Imagens do projeto
│   └── certificates/    # Certificados e diplomas
├── media/
│   ├── videos/          # Vídeos (para futuras versões)
│   └── docs/            # PDFs e documentos
└── config/
    ├── profile.json     # Seus dados pessoais/profissionais
    ├── colors.json      # Paleta de cores do site
    └── fonts/           # Fontes customizadas (.ttf, .otf, .woff)
```

## Como Usar

1. **Edite `config/profile.json`** com seus dados
2. **Edite `config/colors.json`** para personalizar as cores
3. **Adicione suas fotos** em `profile/photos/`
4. **Adicione seu logo** em `profile/logo/`
5. **Crie projetos** em `portfolio/projects/` (cada subpasta é um projeto)
6. **Execute o gerador** para criar o site

## Dicas

- Use imagens de alta qualidade (recomendado: 1200x800px para projetos)
- Nomeie os arquivos de forma descritiva
- Cada projeto deve ter um arquivo `meta.json` com título, descrição e categoria
- Fontes customizadas devem estar em formato .ttf, .otf, .woff ou .woff2
"""
    
    with open(base / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"✅ Estrutura de banco de dados criada em: {base}")
    print("   Edite os arquivos JSON e adicione suas mídias antes de gerar o site.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Profile Analyzer & Static Site Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Criar estrutura inicial do banco de dados
  python analyze_and_generate.py --init ./database

  # Analisar banco de dados e gerar site
  python analyze_and_generate.py --database ./database --output ./site

  # Apenas analisar (sem gerar site)
  python analyze_and_generate.py --database ./database --analyze-only
        """
    )
    
    parser.add_argument('--init', metavar='PATH',
                        help='Criar estrutura inicial do banco de dados')
    parser.add_argument('--database', '-d', metavar='PATH',
                        help='Caminho para o banco de dados de mídia')
    parser.add_argument('--output', '-o', metavar='PATH', default='./site',
                        help='Caminho para o site gerado (padrão: ./site)')
    parser.add_argument('--analyze-only', action='store_true',
                        help='Apenas analisar, sem gerar site')
    
    args = parser.parse_args()
    
    if args.init:
        create_database_structure(args.init)
        return
    
    if not args.database:
        parser.print_help()
        print("\n❌ Erro: Especifique --database ou --init")
        return
    
    # Analisar banco de dados
    analyzer = MediaAnalyzer(args.database)
    result = analyzer.analyze()
    
    if args.analyze_only:
        print("\n📊 Resultado da análise:")
        print(f"   Perfil: {result.profile.name}")
        print(f"   Projetos: {len(result.projects)}")
        print(f"   Posts Instagram: {len(result.instagram_posts)}")
        print(f"   Certificados: {len(result.certificates)}")
        print(f"   Fontes: {len(result.fonts)}")
        return
    
    # Gerar site
    generator = SiteGenerator(result, args.output)
    generator.generate()
    
    print(f"\n🎉 Site gerado com sucesso!")
    print(f"   Para visualizar, abra: {args.output}/index.html")
    print(f"   Ou use um servidor local: python -m http.server -d {args.output}")


if __name__ == '__main__':
    main()
