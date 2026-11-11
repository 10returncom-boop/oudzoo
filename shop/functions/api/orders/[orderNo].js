// Cloudflare Pages Function：GET /api/orders/:orderNo?email=xxx
// 從 KV 取回訂單（需 Email 比對才回，避免知道編號就能看別人的地址）
// 對應檔案：functions/api/orders/[orderNo].js → 路由 /api/orders/任意值

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

export async function onRequestGet({ request, env, params }) {
  if (!env.ORDERS) return json({ ok: false, error: 'ORDERS KV 未綁定' }, 501);

  const orderNo = String((params && params.orderNo) || '').toUpperCase();
  if (!/^SK\d{6}[A-Z0-9]{4}$/.test(orderNo)) return json({ ok: false, error: 'bad orderNo' }, 400);

  const email = (new URL(request.url).searchParams.get('email') || '').trim().toLowerCase();
  if (!email) return json({ ok: false, error: 'need email' }, 400);

  const raw = await env.ORDERS.get('order:' + orderNo);
  if (!raw) return json({ ok: false, error: 'not found' }, 404);

  let order;
  try {
    order = JSON.parse(raw);
  } catch {
    return json({ ok: false, error: 'corrupt record' }, 500);
  }

  const owner = String((order.receiver && order.receiver.email) || '').toLowerCase();
  if (owner !== email) return json({ ok: false, error: 'not found' }, 404);

  return json({ ok: true, order });
}

export async function onRequestPost() {
  return json({ ok: false, error: 'method not allowed' }, 405);
}
