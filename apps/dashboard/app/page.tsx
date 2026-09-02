const cards = [
  ["Channels", "Phone, WhatsApp, web and Telegram feed one customer timeline."],
  ["AI employees", "Reception, sales, booking, support and follow-up work through approvals."],
  ["Control", "Every business action is checked, recorded and reversible where possible."],
];

export default function Home() {
  return (
    <main>
      <header><span className="mark">M</span><div><strong>MBAs</strong><small>MANI Business Automation System</small></div><span className="status">Core online</span></header>
      <section className="hero"><p className="eyebrow">AI workforce platform for Indian businesses</p><h1>One operating system for every customer conversation.</h1><p className="lead">The first deployment connects your business data, automation and AI employees. Voice, WhatsApp and web agents use the same customer memory and safe action gateway.</p><div className="actions"><button>Start business setup</button><a href="/api/healthz">Check system health</a></div></section>
      <section className="grid">{cards.map(([title, copy]) => <article key={title}><h2>{title}</h2><p>{copy}</p></article>)}</section>
      <section className="pilot"><div><p className="eyebrow">First pilot</p><h2>Travel and car rental operations</h2><p>Lead → quote → booking → payment link → WhatsApp confirmation → follow-up.</p></div><ol><li>Business profile and pricing</li><li>Vehicle availability and booking</li><li>Telugu, Hindi and English customer handling</li></ol></section>
    </main>
  );
}

