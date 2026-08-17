import { useParams, Link, Navigate } from 'react-router-dom';
import Shell from '../components/Shell';
import { learnBySlug, LEARN_ARTICLES } from '../content/miLearn';
import { remapLink } from '../lib/mirrorLinks';
import { SITE, breadcrumbJsonLd } from '../lib/siteMeta';

function renderInline(text, keyPrefix) {
  const parts = [];
  const re = /\[([^\]]+)\]\(([^)]+)\)|\*([^*]+)\*/g;
  let last = 0;
  let m;
  let k = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    if (m[1]) {
      parts.push(
        <Link key={`${keyPrefix}-${k++}`} to={remapLink(m[2])} className="underline underline-offset-4 decoration-[#B9B9B0] hover:decoration-[#1C1C18]">
          {m[1]}
        </Link>
      );
    } else {
      parts.push(<em key={`${keyPrefix}-${k++}`}>{m[3]}</em>);
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

const Block = ({ block, i }) => {
  if (block.type === 'h2')
    return <h2 className="mi2-serif text-2xl text-[#1C1C18] mt-10 mb-4">{renderInline(block.text, `h${i}`)}</h2>;
  if (block.type === 'quote')
    return (
      <blockquote className="my-8 border-l-2 border-[#7E8E77] pl-5 mi2-serif text-xl text-[#1C1C18] italic">
        {renderInline(block.text, `q${i}`)}
      </blockquote>
    );
  if (block.type === 'note')
    return (
      <p className="mt-10 border-t border-[#E4E4DE] pt-5 text-xs text-[#6E6E66] leading-relaxed">
        {renderInline(block.text, `n${i}`)}
      </p>
    );
  return <p className="my-4 text-base text-[#3B3B34] leading-[1.75]">{renderInline(block.text, `p${i}`)}</p>;
};

export default function LearnArticle() {
  const { slug } = useParams();
  const article = learnBySlug[slug];
  if (!article) return <Navigate to="/learn" replace />;

  const others = LEARN_ARTICLES.filter((a) => a.slug !== slug).slice(0, 2);
  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: article.h1,
      description: article.description || article.dek,
      author: { '@type': 'Organization', name: SITE.name },
      publisher: { '@type': 'Organization', name: SITE.name },
      mainEntityOfPage: `${SITE.baseUrl}/learn/${slug}`,
    },
    breadcrumbJsonLd([{ name: 'Rather Know', path: '/' }, { name: 'Learn', path: '/learn' }, { name: article.h1 }]),
  ];

  return (
    <Shell title={article.h1} description={article.description || article.dek} jsonLd={jsonLd}>
      <article className="max-w-2xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">
          <Link to="/learn" className="hover:text-[#1C1C18]">Learn</Link> · {article.cluster} · {article.readMins} min
        </p>
        <h1 className="mi2-serif mt-4 text-3xl sm:text-4xl leading-tight text-[#1C1C18]" data-testid="article-h1">
          {article.h1}
        </h1>
        <p className="mt-4 text-lg text-[#6E6E66] leading-relaxed mi2-serif italic">{article.dek}</p>
        <div className="mt-8 border-t border-[#E4E4DE] pt-2" data-testid="article-body">
          {article.body.map((b, i) => <Block key={i} block={b} i={i} />)}
        </div>

        <div className="mt-12 bg-[#1C1C18] text-[#F6F6F2] p-7 flex flex-wrap items-center justify-between gap-4" data-testid="article-cta">
          <p className="mi2-serif text-lg">{article.cta?.title || 'Name the pattern.'}</p>
          <Link to={remapLink(article.cta?.to || '/take/essential')} className="text-sm bg-[#F6F6F2] text-[#1C1C18] px-5 py-2.5 rounded-sm hover:opacity-90">
            {article.cta?.label || 'Start free'}
          </Link>
        </div>

        <div className="mt-12">
          <p className="text-xs uppercase tracking-[0.14em] text-[#6E6E66]">Keep reading</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {others.map((a) => (
              <Link key={a.slug} to={`/learn/${a.slug}`} className="bg-white border border-[#E4E4DE] p-5 hover:shadow-[0_2px_16px_rgba(28,28,24,0.06)]">
                <p className="mi2-serif text-base leading-snug text-[#1C1C18]">{a.h1}</p>
                <p className="mt-2 text-xs text-[#6E6E66]">{a.readMins} min</p>
              </Link>
            ))}
          </div>
        </div>
      </article>
    </Shell>
  );
}
