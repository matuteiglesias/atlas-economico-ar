import Link from "next/link";
export default function Home() {
  return <main className="grid min-h-screen place-items-center"><div><h1 className="font-serif text-5xl">Argentina Economic Atlas</h1><Link className="mt-6 inline-block text-blue-700" href="/topics/inflation">Explore inflation →</Link></div></main>;
}
