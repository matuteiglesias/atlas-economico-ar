import Link from "next/link";
import { SiteHeader } from "@/components/shell";
export default function NotFound() { return <><SiteHeader /><main className="empty-area"><p className="eyebrow">404</p><h2>This atlas page is not available.</h2><p>The route is outside the currently compiled public structure.</p><Link href="/atlas">Browse the atlas →</Link></main></>; }
