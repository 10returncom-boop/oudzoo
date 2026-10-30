/* nav.js — 樹狀側邊欄展開/收合 + 行動漢堡選單 */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    // 側邊欄樹狀導覽
    const tree = document.querySelector(".sidebar .tree");
    if (tree) {
      tree.querySelectorAll(".tree-row").forEach(function (row) {
        row.addEventListener("click", function (e) {
          const li = row.parentElement;
          if (li.querySelector(":scope > ul")) { e.preventDefault(); li.classList.toggle("open"); }
        });
      });
      const cur = tree.querySelector("a.current");
      if (cur) {
        let p = cur.parentElement;
        while (p && p !== tree) {
          if (p.classList && p.classList.contains("tree-item")) p.classList.add("open");
          p = p.parentElement;
        }
      }
    }

    // 行動漢堡選單：把頂部導覽複製進抽屜
    const hamburger = document.querySelector(".hamburger");
    const drawer = document.querySelector(".drawer");
    if (hamburger && drawer) {
      const nav = document.querySelector(".main-nav");
      if (nav) drawer.querySelector(".drawer-inner").innerHTML = nav.outerHTML;
      const backdrop = document.createElement("div");
      backdrop.className = "drawer-backdrop";
      document.body.appendChild(backdrop);
      function close() { drawer.classList.remove("open"); backdrop.classList.remove("open"); }
      hamburger.addEventListener("click", function () { drawer.classList.toggle("open"); backdrop.classList.toggle("open"); });
      backdrop.addEventListener("click", close);
      document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
    }

    // 頂部導覽：點擊固定下拉（再點或點外部/Esc 關閉，避免移開滑鼠就跑掉）
    const topItems = document.querySelectorAll(".main-nav .nav-item");
    if (topItems.length) {
      topItems.forEach(function (item) {
        const label = item.querySelector(":scope > .nav-label");
        if (!label) return;
        label.addEventListener("click", function (e) {
          const wasOpen = item.classList.contains("open");
          topItems.forEach(function (it) { it.classList.remove("open"); });
          if (!wasOpen) item.classList.add("open");
          e.stopPropagation();
        });
      });
      document.addEventListener("click", function (e) {
        if (!e.target.closest(".main-nav .nav-item")) {
          topItems.forEach(function (it) { it.classList.remove("open"); });
        }
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") topItems.forEach(function (it) { it.classList.remove("open"); });
      });
    }
  });
})();
