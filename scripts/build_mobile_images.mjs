import { readFile, writeFile, mkdir, access } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const pages = [
  'realisations/index.html',
  'garde-corps-nice/index.html',
  'portails-sur-mesure-nice/index.html',
  'portes-metalliques-nice/index.html',
  'clotures-fer-forge-nice/index.html',
  'rampes-escalier-nice/index.html',
  'pergolas-marquises-nice/index.html',
];

const heroArt = {
  'realisations/index.html': '../assets/images/mobile/realisations-hero-mobile.webp',
  'garde-corps-nice/index.html': '../assets/images/mobile/garde-corps-hero-mobile.webp',
  'portails-sur-mesure-nice/index.html': '../assets/images/mobile/portails-hero-mobile.webp',
  'portes-metalliques-nice/index.html': '../assets/images/mobile/portes-hero-mobile.webp',
  'clotures-fer-forge-nice/index.html': '../assets/images/mobile/clotures-hero-mobile.webp',
  'rampes-escalier-nice/index.html': '../assets/images/mobile/rampes-hero-mobile.webp',
  'pergolas-marquises-nice/index.html': '../assets/images/mobile/pergolas-hero-mobile.webp',
};

const mobileCss = `<style id="mobile-art-direction">
.mobile-picture{display:block;width:100%;height:100%}.mobile-picture>img{display:block;width:100%;height:100%;object-fit:cover}
.gh-slide>picture,.gh-why .rt-image-mask-wrapper>.mobile-picture{position:absolute;inset:0;width:100%;height:100%}
@media(max-width:767px){
  .rt-section-gap,.rt-section-gap-v2,.rt-section-gap-v3{padding-top:3.5rem!important;padding-bottom:3.5rem!important}
  .rt-container{padding-left:1.125rem!important;padding-right:1.125rem!important}
  .rt-portfolio-image-wrapper-v1,.rt-blog-image-wrapper{aspect-ratio:4/5!important;min-height:0!important}
  .rt-portfolio-image-v1,.rt-blog-image-v1{width:100%!important;height:100%!important;object-fit:cover!important}
  .gh-hero{height:max(43rem,100svh)!important;min-height:43rem}
  .gh-content{left:1.125rem!important;right:1.125rem!important;bottom:6.75rem!important;width:auto!important}
  .gh-title{font-size:clamp(2.25rem,11vw,3.7rem)!important;line-height:.96!important}
  .gh-sub{font-size:1rem!important;line-height:1.45!important}
  .gh-slide picture{position:absolute;inset:0;width:100%;height:100%}
  .gh-slide picture img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .rt-hero-background-image-wrapper-v1 picture{display:block;width:100%;height:100%}
}
</style>`;

const shouldConvert = (tag) =>
  /class="[^"]*(?:rt-portfolio-image-v1|rt-blog-image-v1|gh-why-img)[^"]*"/.test(tag) &&
  !/data-mobile-art/.test(tag);

for (const page of pages) {
  let html = await readFile(page, 'utf8');
  const dir = path.dirname(page);
  if (!html.includes('id="mobile-art-direction"')) html = html.replace('</head>', `${mobileCss}\n</head>`);
  if (!html.includes('data-mobile-hero')) {
    if (page === 'realisations/index.html') {
      html = html.replace(/(<div class="rt-hero-background-image-wrapper-v1">\s*)(<img\b[^>]*class="rt-hero-background-image"[^>]*>)/, `$1<picture data-mobile-hero class="mobile-picture"><source media="(max-width: 767px)" srcset="${heroArt[page]}">$2</picture>`);
    } else {
      html = html.replace(/(<div class="gh-slide is-active"[^>]*>)(<img\b[^>]*>)/, `$1<picture data-mobile-hero><source media="(max-width: 767px)" srcset="${heroArt[page]}">$2</picture>`);
    }
  }
  const tags = [...html.matchAll(/<img\b[^>]*>/g)].map((m) => m[0]).filter(shouldConvert);
  for (const tag of tags) {
    const src = tag.match(/\bsrc="([^"]+)"/)?.[1];
    if (!src || !/\.(?:webp|jpe?g|png)$/i.test(src)) continue;
    const input = path.resolve(dir, src);
    const parsed = path.parse(input);
    const output = path.join(parsed.dir, `${parsed.name}-mobile.webp`);
    try { await access(output); } catch {
      await mkdir(parsed.dir, { recursive: true });
      const result = spawnSync('cwebp', ['-quiet', '-q', '82', '-resize', '720', '0', input, '-o', output], { stdio: 'inherit' });
      if (result.status !== 0) throw new Error(`cwebp failed for ${input}`);
    }
    const mobileSrc = path.relative(dir, output).split(path.sep).join('/');
    const picture = `<picture class="mobile-picture"><source media="(max-width: 767px)" srcset="${mobileSrc}">${tag.replace('<img ', '<img data-mobile-art="true" ')}</picture>`;
    html = html.replace(tag, picture);
  }
  await writeFile(page, html);
}
