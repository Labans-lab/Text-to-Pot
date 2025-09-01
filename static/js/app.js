// app.js - front-end behaviour for TEXT TO POT
const suggestBtn = document.getElementById("suggestBtn");
const refreshBtn = document.getElementById("refreshBtn");
const ingredientsEl = document.getElementById("ingredients");
const recipesGrid = document.getElementById("recipesGrid");
const statusEl = document.getElementById("status");

async function setStatus(msg, isError=false) {
  statusEl.textContent = msg || "";
  statusEl.style.color = isError ? "#b91c1c" : "";
}

function renderRecipes(recipes){
  recipesGrid.innerHTML = "";
  if(!recipes || recipes.length === 0){
    recipesGrid.innerHTML = `<div class="card muted">No recipes yet. Try entering ingredients and click "Suggest Recipes".</div>`;
    return;
  }
  recipes.forEach(r=>{
    const card = document.createElement("div");
    card.className = "recipe-card";
    card.innerHTML = `
      <h4>${escapeHtml(r.title)}</h4>
      <div class="meta">Source: ${escapeHtml(r.source || 'TEXT TO POT')} • ${new Date(r.created_at).toLocaleString()}</div>
      <p><strong>Ingredients:</strong> ${escapeHtml(r.ingredients)}</p>
      <p><strong>Instructions:</strong><br/> ${escapeHtml(r.instructions)}</p>
      <div class="small">ID: ${r.id}</div>
    `;
    recipesGrid.appendChild(card);
  });
}

function escapeHtml(text){
  if(!text) return "";
  return text.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
}

async function fetchRecipes(){
  setStatus("Loading saved recipes...");
  try {
    const res = await fetch("/api/recipes");
    const data = await res.json();
    if(data.ok){
      renderRecipes(data.recipes || []);
      setStatus("");
    } else {
      setStatus("Failed to fetch recipes", true);
    }
  } catch (e) {
    setStatus("Error loading recipes", true);
    console.error(e);
  }
}

suggestBtn?.addEventListener("click", async ()=>{
  const ingredients = ingredientsEl.value.trim();
  if(!ingredients){
    setStatus("Please enter at least one ingredient.", true);
    return;
  }
  setStatus("Generating recipes... please wait (may take a few seconds)...");
  suggestBtn.disabled = true;
  try {
    const res = await fetch("/api/suggest", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ingredients})
    });
    const data = await res.json();
    if(!data.ok){
      setStatus((data.error || "Failed to generate recipes"), true);
    } else {
      setStatus("Recipes saved. Refreshing list...");
      await fetchRecipes();
      setStatus("Done.");
    }
  } catch (e) {
    setStatus("Network error: could not reach server", true);
    console.error(e);
  } finally {
    suggestBtn.disabled = false;
  }
});

refreshBtn?.addEventListener("click", fetchRecipes);

// initial load
fetchRecipes();
