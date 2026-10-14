import { isConfigured, addMessage, updateMessage, deleteMessage, watchMessages } from "./db.js";

const form = document.getElementById("message-form");
const list = document.getElementById("message-list");
const notice = document.getElementById("notice");

function showNotice(text, isError = false) {
  notice.textContent = text;
  notice.classList.toggle("error", isError);
  notice.hidden = !text;
}

function formatTime(ts) {
  // createdAt is null for a moment while the server timestamp is pending.
  return ts ? ts.toDate().toLocaleString("zh-TW") : "送出中…";
}

function el(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
}

async function run(action) {
  try {
    await action();
    showNotice("");
  } catch (err) {
    console.error(err);
    showNotice(`操作失敗:${err.message}`, true);
  }
}

function renderItem(msg) {
  const meta = el("div", { className: "meta" },
    el("span", { className: "author" }, msg.name),
    ` · ${formatTime(msg.createdAt)}`,
    msg.updatedAt ? "(已編輯)" : "",
  );
  const body = el("p", { className: "body" }, msg.text);

  const editBtn = el("button", { type: "button" }, "編輯");
  const deleteBtn = el("button", { type: "button" }, "刪除");
  const actions = el("div", { className: "actions" }, editBtn, deleteBtn);
  const item = el("li", {}, meta, body, actions);

  deleteBtn.addEventListener("click", () => {
    if (confirm("確定要刪除這則留言?")) run(() => deleteMessage(msg.id));
  });

  editBtn.addEventListener("click", () => {
    const textarea = el("textarea", { rows: 3, maxLength: 500, value: msg.text });
    const saveBtn = el("button", { type: "button" }, "儲存");
    const cancelBtn = el("button", { type: "button" }, "取消");
    item.replaceChildren(meta, textarea, el("div", { className: "actions" }, saveBtn, cancelBtn));

    cancelBtn.addEventListener("click", () => item.replaceWith(renderItem(msg)));
    saveBtn.addEventListener("click", () => {
      const text = textarea.value.trim();
      if (text) run(() => updateMessage(msg.id, text));
    });
  });

  return item;
}

function render(messages) {
  if (messages.length === 0) {
    list.replaceChildren(el("li", { className: "empty" }, "還沒有留言"));
    return;
  }
  list.replaceChildren(...messages.map(renderItem));
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const name = form.name.value.trim();
  const text = form.text.value.trim();
  if (!name || !text) return;
  run(async () => {
    await addMessage(name, text);
    form.text.value = "";
  });
});

if (isConfigured) {
  watchMessages(render, (err) => {
    console.error(err);
    showNotice(`讀取留言失敗:${err.message}`, true);
  });
} else {
  showNotice("尚未設定 Firebase:請在 firebase-config.js 填入開發用專案的設定。", false);
  form.querySelectorAll("input, textarea, button").forEach((control) => { control.disabled = true; });
  render([]);
}
