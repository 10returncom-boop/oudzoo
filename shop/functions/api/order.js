// Cloudflare Pages Function：POST /api/order
// 收前端送出的訂單 → 驗證 → 存進 KV（若有綁定）→ 寄信（若有金鑰）
//
// 環境變數（Pages 專案 → Settings → Environment variables）：
//   ORDER_TO         收件信箱（不設就只驗證、不寄信）
//   RESEND_API_KEY   Resend API key（不設就只驗證、不寄信）
//   ORDER_FROM       寄件人，例如 "ShopKit <orders@你的網域>"
// KV 命名空間綁定（選用，綁了才能用 GET /api/orders/:no 跨裝置查）：
//   ORDERS           Workers KV namespace

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

const bad = (msg) => json({ ok: false, error: msg }, 400);
const str = (v, max = 120) => (typeof v === 'string' ? v.slice(0, max) : '');
const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? Math.max(0, Math.round(v)) : 0);

function maskPhone(phone) {
  const p = String(phone || '');
  return /^\d{10}$/.test(p) ? p.slice(0, 4) + '***' + p.slice(-3) : '***';
}

function publicOrder(order) {
  const receiver = order.receiver || {};
  return {
    orderNo: String(order.orderNo),
    createdAt: str(order.createdAt, 40),
    status: str(order.status, 20) || 'pending',
    statusLabel: str(order.statusLabel, 40) || '待確認付款',
    items: (order.items || []).slice(0, 60).map((it) => ({
      sku: str(it.sku, 40),
      name: str(it.name, 100),
      optionLabel: str(it.optionLabel, 80),
      qty: Math.min(99, num(it.qty)),
      price: num(it.price),
    })),
    totals: {
      subtotal: num(order.totals && order.totals.subtotal),
      discount: num(order.totals && order.totals.discount),
      shipping: num(order.totals && order.totals.shipping),
      tax: num(order.totals && order.totals.tax),
      total: num(order.totals && order.totals.total),
    },
    coupon: str(order.coupon, 30),
    receiver: {
      name: str(receiver.name, 40),
      email: str(receiver.email, 120),
      phone: maskPhone(receiver.phone),
    },
    shipMethodName: str(order.shipMethodName, 40),
    shipEta: str(order.shipEta, 40),
    addressText: str(order.addressText, 160),
    invoiceText: str(order.invoiceText, 120),
  };
}

export async function onRequestPost({ request, env }) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return bad('invalid json');
  }

  const order = payload && payload.order;
  if (!order || !order.orderNo) return bad('missing order');
  if (!/^SK\d{6}[A-Z0-9]{4}$/.test(String(order.orderNo))) return bad('bad orderNo');

  const receiver = order.receiver || {};
  const phoneOk = /^09\d{8}$/.test(String(receiver.phone || ''));
  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(receiver.email || ''));
  if (!receiver.name || !phoneOk || !emailOk) return bad('bad receiver');
  if (!order.totals || typeof order.totals.total !== 'number' || order.totals.total < 0 || order.totals.total > 1000000) {
    return bad('bad totals');
  }
  if (!Array.isArray(order.items) || order.items.length === 0 || order.items.length > 60) return bad('bad items');

  const stored = publicOrder(order);
  let kvStored = false;

  if (env.ORDERS) {
    // 同一編號不覆蓋既有訂單（避免重送改掉金額）
    const exist = await env.ORDERS.get('order:' + stored.orderNo);
    if (!exist) {
      await env.ORDERS.put('order:' + stored.orderNo, JSON.stringify(stored), { expirationTtl: 60 * 60 * 24 * 180 });
    }
    kvStored = true;
  }

  const subject = str(payload.subject, 160) || `新訂單 ${stored.orderNo}`;
  const text = str(payload.body, 6000) || JSON.stringify(stored, null, 2);

  if (!env.ORDER_TO || !env.RESEND_API_KEY) {
    return json({
      ok: true,
      stored: kvStored,
      emailed: false,
      note: !env.ORDER_TO ? 'ORDER_TO 未設定，只存不寄' : 'RESEND_API_KEY 未設定，只存不寄',
    });
  }

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.RESEND_API_KEY}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      from: env.ORDER_FROM || 'ShopKit <onboarding@resend.dev>',
      to: [env.ORDER_TO],
      reply_to: stored.receiver.email,
      subject,
      text,
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    return json({ ok: false, stored: kvStored, emailed: false, error: 'mail send failed', detail: detail.slice(0, 300) }, 502);
  }

  return json({ ok: true, stored: kvStored, emailed: true, id: (await res.json()).id || null });
}

export async function onRequestGet() {
  return json({ ok: false, error: 'method not allowed' }, 405);
}
