import { apiGet } from "./api";

export interface Custodian {
  name: string;
  value: number;
  verified: boolean;
}

export interface PortfolioSummary {
  total_assets: number;
  currency: string;
  custodians: Custodian[];
}

export function getPortfolioSummary() {
  return apiGet<PortfolioSummary>("/api/portfolio/summary");
}
