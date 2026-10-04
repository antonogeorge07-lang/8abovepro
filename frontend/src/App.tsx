import {
  ArrowRight,
  CircleUserRound,
  Landmark,
  Leaf,
  Scale,
  Sparkles,
} from "lucide-react";

type ChangeRow = {
  label: string;
  value: string;
  tone?: "positive" | "calm" | "attention";
};

const changes: ChangeRow[] = [
  {
    label: "Swiss custody",
    value: "+ €2.4M",
    tone: "positive",
  },
  {
    label: "Liquidity",
    value: "Within target",
    tone: "calm",
  },
  {
    label: "Regulatory exposure",
    value: "1 item to review",
    tone: "attention",
  },
];

export default function App() {
  return (
    <div className="prosperity-app">
      <header className="topbar">
        <a className="identity-mark" href="/" aria-label="8above home">
          <span className="identity-symbol">8</span>
          <span className="identity-wordmark">above</span>
        </a>

        <nav className="primary-nav" aria-label="Primary">
          <button className="nav-item is-active" type="button">
            Today
          </button>
          <button className="nav-item" type="button">
            Wealth
          </button>
          <button className="nav-item" type="button">
            Decisions
          </button>
          <button className="nav-item" type="button">
            People
          </button>
        </nav>

        <button className="profile-trigger" type="button" aria-label="Open account">
          <span>AG</span>
        </button>
      </header>

      <main className="today">
        <section className="opening-field">
          <p className="day-context">Sunday · 4 October</p>

          <h1>
            Good afternoon.
          </h1>

          <p className="state-line">
            Your position is steady.
          </p>

          <div className="position">
            <span className="currency">€</span>
            <span className="position-value">142,850,420</span>
          </div>

          <div className="position-context">
            <span className="growth-mark">
              <Leaf size={15} strokeWidth={1.8} />
              + €1.84M this month
            </span>

            <span className="quiet-dot" aria-hidden="true" />

            <span>Updated 6 minutes ago</span>
          </div>
        </section>

        <section className="change-field">
          <div className="section-intro">
            <span className="section-number">01</span>
            <h2>What changed</h2>
          </div>

          <div className="change-list">
            {changes.map((item) => (
              <div className="change-row" key={item.label}>
                <span className="change-label">{item.label}</span>
                <span
                  className={[
                    "change-value",
                    item.tone ? `tone-${item.tone}` : "",
                  ].join(" ")}
                >
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="attention-field">
          <div className="section-intro">
            <span className="section-number">02</span>
            <h2>What needs you</h2>
          </div>

          <article className="focus-field">
            <div className="focus-symbol">
              <Scale size={22} strokeWidth={1.65} />
            </div>

            <div className="focus-copy">
              <span className="focus-category">
                Regulatory exposure
              </span>

              <h3>Swiss FADP update</h3>

              <p>
                A policy change may affect one holding.
                Review the impact when you are ready.
              </p>
            </div>

            <button className="focus-action" type="button">
              Review
              <ArrowRight size={17} />
            </button>
          </article>
        </section>

        <section className="world-field">
          <div className="section-intro">
            <span className="section-number">03</span>
            <h2>Your financial world</h2>
          </div>

          <div className="world-line">
            <div className="world-item">
              <Landmark size={17} strokeWidth={1.6} />
              <div>
                <strong>Switzerland</strong>
                <span>Primary custody</span>
              </div>
            </div>

            <div className="world-item">
              <Sparkles size={17} strokeWidth={1.6} />
              <div>
                <strong>UAE</strong>
                <span>Regional position</span>
              </div>
            </div>

            <div className="world-item">
              <CircleUserRound size={17} strokeWidth={1.6} />
              <div>
                <strong>2 people</strong>
                <span>Active access</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
