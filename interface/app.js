/* TitonTambouille — interface (JavaScript sans dépendance).
 * Tout le texte venant du journal est inséré comme texte (jamais comme HTML).
 */
"use strict";

// ------------------------------------------------------------------ outils

function h(balise, attrs, ...enfants) {
  const el = document.createElement(balise);
  for (const [cle, val] of Object.entries(attrs || {})) {
    if (val === null || val === undefined || val === false) continue;
    if (cle.startsWith("on")) el.addEventListener(cle.slice(2).toLowerCase(), val);
    else if (cle === "class") el.className = val;
    else el.setAttribute(cle, val === true ? "" : val);
  }
  for (const enfant of enfants.flat(Infinity)) {
    if (enfant === null || enfant === undefined || enfant === false) continue;
    el.append(enfant instanceof Node ? enfant : document.createTextNode(String(enfant)));
  }
  return el;
}

function svg(chemins, taille = 20, epaisseur = 1.6) {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("width", taille); s.setAttribute("height", taille);
  s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none");
  s.setAttribute("stroke", "currentColor"); s.setAttribute("stroke-width", epaisseur);
  s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
  s.setAttribute("aria-hidden", "true");
  s.innerHTML = chemins;          // constantes du code uniquement
  return s;
}

const ICONES = {
  journal: '<path d="M4 20h4L19 9l-4-4L4 16z"></path><path d="M13.5 6.5l4 4"></path>',
  recettes: '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"></path><path d="M5 17a3 3 0 0 1 3-3h11"></path>',
  idees: '<path d="M9 18h6"></path><path d="M10 21h4"></path><path d="M12 3a6 6 0 0 0-3.5 10.9V16h7v-2.1A6 6 0 0 0 12 3z"></path>',
  ardoise: '<rect x="3" y="5" width="18" height="14"></rect><path d="M7 9h6"></path><path d="M7 12h10"></path><path d="M7 15h4"></path>',
  carte: '<path d="M12 21s-6-5.6-6-11a6 6 0 0 1 12 0c0 5.4-6 11-6 11z"></path><circle cx="12" cy="10" r="2.2"></circle>',
  photo: '<path d="M4 7h3l2-2h6l2 2h3v12H4z"></path><circle cx="12" cy="13" r="3.5"></circle>',
  lien: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"></path><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"></path>',
  croix: '<path d="M6 6l12 12M18 6L6 18"></path>',
  autre: '<path d="M20 12a8 8 0 1 1-2.3-5.7"></path><path d="M20 4v5h-5"></path>',
};

const JOURS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
const MOIS_COURT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];

function dateDe(iso) { const [a, m, j] = iso.split("-").map(Number); return new Date(a, m - 1, j); }
function dateLongue(iso) { const d = dateDe(iso); return `${JOURS[d.getDay()]} ${d.getDate()} ${MOIS[d.getMonth()]}`; }
function dateCourte(iso) { const d = dateDe(iso); return `${d.getDate() === 1 ? "1er" : d.getDate()} ${MOIS_COURT[d.getMonth()]}`; }
function heureLisible(hm) { const [hh, mm] = hm.split(":"); return `${Number(hh)} h ${mm}`; }
function aujourdhui() { const d = new Date(); return `${JOURS[d.getDay()]} ${d.getDate()} ${MOIS[d.getMonth()]} ${d.getFullYear()}`; }
function moisCourant() { return new Date().getMonth() + 1; }
function domaine(url) { try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; } }
function premiereMajuscule(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function annoncer(texte) {
  const m = document.getElementById("message");
  m.textContent = texte; m.hidden = false;
  clearTimeout(annoncer.minuterie);
  annoncer.minuterie = setTimeout(() => { m.hidden = true; }, 3500);
}

async function api(chemin, options) {
  const rep = await fetch(chemin, options);
  const donnees = await rep.json().catch(() => ({}));
  if (!rep.ok) throw new Error(donnees.erreur || `Erreur ${rep.status}`);
  return donnees;
}

// ------------------------------------------------------------------ navigation

const ONGLETS = [
  { id: "journal", nom: "Journal" },
  { id: "recettes", nom: "Recettes" },
  { id: "idees", nom: "Idées" },
  { id: "ardoise", nom: "Ardoise" },
  { id: "carte", nom: "Carte" },
];

const etat = { onglet: "journal", entrees: [], digestion: null, onglets: null, recette: null, recherche: "", filtreIdees: "a_tester", filtreLieux: "tout" };

function construireNavigation() {
  for (const nav of document.querySelectorAll(".onglets")) {
    nav.replaceChildren(...ONGLETS.map(o =>
      h("a", { href: `#${o.id}`, "data-onglet": o.id }, h("span", { class: "ico" }, svg(ICONES[o.id], 24, 1.7)), h("span", {}, o.nom))));
  }
}

function majNavigation() {
  for (const a of document.querySelectorAll(".onglets a")) {
    if (a.dataset.onglet === etat.onglet) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
  document.querySelector(".page").classList.toggle("large", ["recettes", "carte"].includes(etat.onglet));
}

async function changerOnglet() {
  const id = (location.hash || "#journal").slice(1);
  etat.onglet = ONGLETS.some(o => o.id === id) ? id : "journal";
  majNavigation();
  if (etat.onglet !== "journal" && !etat.onglets) {
    try { etat.onglets = await api("/api/onglets"); }
    catch (e) { annoncer(`Impossible de charger les onglets : ${e.message}`); return; }
  }
  afficher();
}

function afficher() {
  const vue = document.getElementById("vue");
  const rendus = { journal: vueJournal, recettes: vueRecettes, idees: vueIdees, ardoise: vueArdoise, carte: vueCarte };
  vue.replaceChildren(...[rendus[etat.onglet]()].flat().filter(x => x !== null && x !== undefined && x !== false));
  const titre = ONGLETS.find(o => o.id === etat.onglet).nom;
  document.title = `${titre} · TitonTambouille`;
}

function titreVue(texte, sousTexte) {
  return h("header", { class: "titre-vue" }, h("h1", {}, texte), sousTexte ? h("p", {}, sousTexte) : null);
}

function bandeauExemple(nom) {
  if (!etat.onglets || !etat.onglets.exemples.includes(nom)) return null;
  return h("p", { class: "bandeau-exemple" }, "Données d'exemple : cet onglet se remplira avec la digestion du journal.");
}

// ------------------------------------------------------------------ journal

const brouillon = { photos: [], liens: [], lienOuvert: false };

function vueJournal() {
  const zone = h("textarea", { id: "entree", rows: 5, placeholder: "Quelques lignes…" });
  zone.value = brouillon.texte || "";
  zone.addEventListener("input", () => { brouillon.texte = zone.value; });
  zone.addEventListener("keydown", e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); noter(); } });

  const choixPhotos = h("input", { type: "file", accept: "image/*", multiple: true, class: "visuellement-cache", id: "choix-photos", tabindex: "-1" });
  choixPhotos.addEventListener("change", () => { ajouterPhotos(choixPhotos.files); choixPhotos.value = ""; });

  const formulaire = h("form", { class: "saisie", onsubmit: e => { e.preventDefault(); noter(); } },
    h("label", { for: "entree", class: "etiquette" }, "Nouvelle entrée"),
    zone,
    h("div", { class: "en-attente", id: "photos-attente" }),
    zoneLien(),
    h("ul", { class: "liens-attente", id: "liens-attente", "aria-label": "Liens à joindre" }),
    h("div", { class: "actions" },
      h("div", { class: "outils" },
        h("button", { type: "button", class: "bouton-icone", "aria-label": "Ajouter une photo", onclick: () => choixPhotos.click() }, svg(ICONES.photo)),
        h("button", { type: "button", class: "bouton-icone", "aria-label": "Ajouter un lien", "aria-pressed": String(brouillon.lienOuvert), id: "bouton-lien",
          onclick: () => { brouillon.lienOuvert = !brouillon.lienOuvert; majBrouillon(); if (brouillon.lienOuvert) document.getElementById("lien-url").focus(); } }, svg(ICONES.lien)),
        choixPhotos),
      h("button", { type: "submit", class: "bouton", id: "noter" }, "Noter")));

  const vue = [titreVue("Journal", aujourdhui()), formulaire, panneauDigestion(), listeJours()];
  queueMicrotask(majBrouillon);
  return vue;
}

function zoneLien() {
  const url = h("input", { type: "url", id: "lien-url", placeholder: "https://…", "aria-label": "Adresse du lien" });
  const titre = h("input", { type: "text", id: "lien-titre", placeholder: "Titre (facultatif)", "aria-label": "Titre du lien" });
  const ajouter = () => {
    const u = url.value.trim();
    if (!/^https?:\/\/\S+$/.test(u)) { annoncer("Le lien doit commencer par http:// ou https://"); url.focus(); return; }
    brouillon.liens.push({ url: u, titre: titre.value.trim() });
    url.value = ""; titre.value = ""; majBrouillon(); url.focus();
  };
  for (const champ of [url, titre]) champ.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ajouter(); } });
  return h("div", { class: "ajout-lien", id: "zone-lien" }, url, titre, h("button", { type: "button", class: "bouton-texte", onclick: ajouter }, "Joindre"));
}

function ajouterPhotos(fichiers) {
  for (const f of fichiers) {
    if (!f.type.startsWith("image/") && !/\.heic$/i.test(f.name)) continue;
    brouillon.photos.push({ fichier: f, apercu: URL.createObjectURL(f), legende: "" });
  }
  majBrouillon();
}

function majBrouillon() {
  const zonePhotos = document.getElementById("photos-attente");
  if (!zonePhotos) return;
  zonePhotos.replaceChildren(...brouillon.photos.map((p, i) => {
    const legende = h("input", { type: "text", placeholder: "légende", value: p.legende, "aria-label": `Légende de la photo ${i + 1}` });
    legende.addEventListener("input", () => { p.legende = legende.value; });
    return h("div", { class: "vignette-attente" },
      h("img", { src: p.apercu, alt: "" }),
      h("button", { type: "button", class: "retirer", "aria-label": `Retirer la photo ${i + 1}`, onclick: () => { URL.revokeObjectURL(p.apercu); brouillon.photos.splice(i, 1); majBrouillon(); } }, svg(ICONES.croix, 14)),
      legende);
  }));
  document.getElementById("liens-attente").replaceChildren(...brouillon.liens.map((l, i) =>
    h("li", {}, svg(ICONES.lien, 16), h("span", {}, l.titre || domaine(l.url)),
      h("button", { type: "button", class: "retirer", "aria-label": `Retirer le lien ${l.titre || l.url}`, onclick: () => { brouillon.liens.splice(i, 1); majBrouillon(); } }, svg(ICONES.croix, 14)))));
  document.getElementById("zone-lien").hidden = !brouillon.lienOuvert;
  document.getElementById("bouton-lien").setAttribute("aria-pressed", String(brouillon.lienOuvert));
}

async function noter() {
  const texte = (brouillon.texte || "").trim();
  if (!texte && !brouillon.photos.length && !brouillon.liens.length) { annoncer("Écris quelques lignes d'abord."); return; }
  const bouton = document.getElementById("noter");
  bouton.disabled = true; bouton.textContent = "…";
  try {
    const photos = [];
    for (const p of brouillon.photos) {
      const rep = await api("/api/photos", { method: "POST", headers: { "X-Nom-Fichier": encodeURIComponent(p.fichier.name || "photo.jpg") }, body: p.fichier });
      photos.push({ fichier: rep.fichier, legende: p.legende.trim() });
    }
    await api("/api/journal", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ texte, photos, liens: brouillon.liens }) });
    for (const p of brouillon.photos) URL.revokeObjectURL(p.apercu);
    Object.assign(brouillon, { texte: "", photos: [], liens: [], lienOuvert: false });
    await chargerJournal();
    afficher();
    annoncer("C'est noté.");
  } catch (e) {
    annoncer(`Pas enregistré : ${e.message}`);
    bouton.disabled = false; bouton.textContent = "Noter";
  }
}

function listeJours() {
  if (!etat.entrees.length) return h("p", { class: "vide" }, "Le journal est encore vide. La première entrée s'affichera ici.");
  const parJour = new Map();
  for (const e of etat.entrees) { if (!parJour.has(e.jour)) parJour.set(e.jour, []); parJour.get(e.jour).push(e); }
  const jours = [...parJour.keys()].sort().reverse();
  return h("section", { class: "jours", "aria-label": "Entrées précédentes" }, jours.map(jour =>
    h("article", { class: "jour" },
      h("h2", { class: "titre-jour" }, premiereMajuscule(dateLongue(jour))),
      parJour.get(jour).slice().reverse().map(vueEntree))));
}

function vueEntree(e) {
  const medias = [];
  if (e.photos.length) medias.push(...e.photos.map(p =>
    h("figure", { class: "vignette" },
      h("a", { href: `/${p.fichier}`, target: "_blank", rel: "noopener" }, h("img", { src: `/${p.fichier}`, alt: p.legende || "photo", loading: "lazy" })),
      p.legende ? h("figcaption", {}, p.legende) : null)));
  if (e.liens.length) medias.push(h("ul", { class: "liens", "aria-label": "Liens" }, e.liens.map(l =>
    h("li", {}, h("a", { href: l.url, target: "_blank", rel: "noopener noreferrer" },
      svg(ICONES.lien, 16), h("span", { class: "titre" }, l.titre || domaine(l.url)), l.titre ? h("span", { class: "domaine" }, domaine(l.url)) : null)))));
  return h("div", { class: "entree" },
    h("span", { class: "heure" }, heureLisible(e.heure)),
    e.texte ? h("p", { class: "texte" }, e.texte) : null,
    medias.length ? h("div", { class: "medias" }, medias) : null);
}

async function chargerJournal() {
  const [d, g] = await Promise.all([api("/api/journal"), api("/api/digestion").catch(() => null)]);
  etat.entrees = d.entrees;
  etat.digestion = g;
}

function dateHeure(iso) {
  const d = new Date(iso);
  return `${d.getDate() === 1 ? "1er" : d.getDate()} ${MOIS_COURT[d.getMonth()]} à ${d.getHours()} h ${String(d.getMinutes()).padStart(2, "0")}`;
}

function panneauDigestion() {
  const g = etat.digestion;
  if (!g) return null;
  const derniere = (g.historique || []).find(d => !d.annulee);
  const enAttente = g.a_digerer ? h("p", { class: "attente-digestion" },
    `${g.a_digerer} entrée${g.a_digerer > 1 ? "s" : ""} pas encore digérée${g.a_digerer > 1 ? "s" : ""} · demande à Claude : « digère TitonTambouille »`) : null;
  if (!derniere) return enAttente ? h("section", { class: "digestion", "aria-label": "Digestion" }, enAttente) : null;
  const bouton = h("button", { type: "button", class: "bouton-texte" }, "Annuler cette digestion");
  bouton.addEventListener("click", async () => {
    if (!bouton.dataset.confirme) { bouton.dataset.confirme = "1"; bouton.textContent = "Confirmer l'annulation"; return; }
    try { await api("/api/digestion/annuler", { method: "POST" }); etat.onglets = null; await chargerJournal(); afficher(); annoncer("Digestion annulée."); }
    catch (e) { annoncer(`Annulation impossible : ${e.message}`); }
  });
  const n = derniere.modifications.length;
  return h("section", { class: "digestion", "aria-label": "Digestion" },
    enAttente,
    h("details", {},
      h("summary", {}, `Dernière digestion · ${dateHeure(derniere.date)} · ${n} modification${n > 1 ? "s" : ""}`),
      h("ul", {}, derniere.modifications.map(m => h("li", {}, m))),
      bouton));
}

// ------------------------------------------------------------------ recettes

function enSaison(saison) { return !saison || !saison.mois || saison.mois.includes(moisCourant()); }

function vueRecettes() {
  const donnees = (etat.onglets.recettes || {}).recettes || [];
  if (!etat.recette && donnees.length) etat.recette = donnees[0].id;
  const recherche = h("input", { type: "search", id: "cherche-r", placeholder: "dahl, soupe, aubergine…", value: etat.recherche });
  const index = h("div", { id: "index-liste", style: "display: flex; flex-direction: column; gap: 16px" });
  const majIndex = () => {
    const q = etat.recherche.trim().toLowerCase();
    const visibles = donnees.filter(r => !q || r.nom.toLowerCase().includes(q));
    const cats = [...new Set(visibles.map(r => r.categorie || "Autres"))];
    index.replaceChildren(...cats.map(cat => h("div", { style: "display: flex; flex-direction: column; gap: 4px" },
      h("h2", { class: "titre-jour" }, cat),
      h("ul", {}, visibles.filter(r => (r.categorie || "Autres") === cat).map(r => {
        const hors = !enSaison(r.saison);
        const meta = hors ? `hors saison · ${r.saison.texte}` : (r.fois ? `${r.fois} fois · ${dateCourte(r.derniere)}` : "pas encore cuisinée");
        return h("li", {}, h("a", { href: "#recettes", class: hors ? "hors-saison" : null, "aria-current": r.id === etat.recette ? "true" : null,
          onclick: ev => { ev.preventDefault(); etat.recette = r.id; afficher(); } },
          h("span", { class: "nom" }, r.nom), h("span", { class: "meta" }, meta)));
      })))));
    if (!visibles.length) index.replaceChildren(h("p", { class: "vide" }, "Aucune recette ne correspond."));
  };
  recherche.addEventListener("input", () => { etat.recherche = recherche.value; majIndex(); });
  majIndex();

  const choisie = donnees.find(r => r.id === etat.recette);
  return h("div", { class: "recettes" },
    h("aside", { class: "index", "aria-label": "Index des recettes" }, h("label", { for: "cherche-r", class: "etiquette" }, "Chercher"), recherche, index),
    h("div", { class: "colonne-recette" },
      h("h1", { class: "titre-vue" }, "Recettes"),
      bandeauExemple("recettes"),
      choisie ? ficheRecette(choisie) : h("p", { class: "vide" }, "Aucune recette pour l'instant.")));
}

function cases(n) {
  return h("span", { class: "cases", "aria-hidden": "true" }, [1, 2, 3].map(i => h("span", { class: i <= n ? "plein" : null })));
}

function goutsFoyer() {
  const membres = ((etat.onglets.foyer || {}).membres || []).filter(m => (m.gouts || []).length);
  if (!membres.length) return null;
  return h("section", { class: "gouts", "aria-label": "Goûts du foyer" },
    h("h2", { class: "titre-jour" }, "Goûts du foyer"),
    membres.map(m => h("div", { class: "gouts-membre" }, h("b", {}, m.initiale),
      h("ul", {}, m.gouts.slice().sort((a, b) => b.niveau - a.niveau).map(g =>
        h("li", { title: g.note || null }, h("span", { role: "img", "aria-label": `${g.niveau} sur 3` }, cases(g.niveau)), h("span", {}, g.aliment)))))));
}

function ficheRecette(r) {
  const membres = ((etat.onglets.foyer || {}).membres || []).map(m => m.initiale);
  const lignes = [];
  if (r.saison) lignes.push(h("div", {}, h("span", { class: "lib" }, "Saison"),
    h("span", { class: "mois", "aria-hidden": "true" }, "JFMAMJJASOND".split("").map((l, i) => h("span", { class: r.saison.mois.includes(i + 1) ? "oui" : null }, l))),
    h("span", { class: "mois-texte" }, r.saison.texte)));
  if (r.regime) lignes.push(h("div", {}, h("span", { class: "lib" }, "Régime"), h("span", { class: "val" }, r.regime)));
  if (r.foyer && membres.some(m => r.foyer[m])) lignes.push(h("div", {}, h("span", { class: "lib" }, "Au foyer"),
    h("span", { class: "foyer" }, membres.filter(m => r.foyer[m]).map(m => {
      const n = r.foyer[m];
      return h("span", { class: "avis", role: "img", "aria-label": `${m} : ${n} sur 3` }, h("b", {}, m),
        h("span", { class: "cases" }, [1, 2, 3].map(i => h("span", { class: i <= n ? "plein" : null }))));
    }))));
  if (r.cout) lignes.push(h("div", {}, h("span", { class: "lib" }, "Coût"),
    h("span", { class: "val cout", "aria-label": `Coût : ${r.cout} sur 3` }, "€".repeat(r.cout), h("span", { class: "eteint", "aria-hidden": "true" }, "€".repeat(3 - r.cout)))));

  const aDesCorrections = (r.ingredients || []).some(i => i.correction);
  const cadre = (r.ingredients && r.ingredients.length) || (r.etapes && r.etapes.length) ? h("section", { class: "cadre" },
    h("div", { class: "cadre-tete" }, h("h3", {}, "La recette"),
      r.source ? h("span", { class: "source" }, "d'après ", r.source.url ? h("a", { href: r.source.url, target: "_blank", rel: "noopener noreferrer" }, r.source.titre) : r.source.titre, r.source.date ? `, ${dateCourte(r.source.date)}` : "") : null),
    h("div", { style: "display: flex; flex-direction: column; gap: 6px" },
      (r.pour || aDesCorrections) ? h("div", { class: "cadre-tete" }, h("span", { class: "mois-texte" }, r.pour || ""),
        aDesCorrections ? h("span", { class: "legende-corr" }, "barré : la source · ", h("strong", {}, "en couleur"), " : tes corrections") : null) : null,
      h("ul", { class: "ingredients" }, (r.ingredients || []).map(i => h("li", {},
        i.correction ? h("span", {}, h("s", {}, i.correction.ancien), " ", h("strong", {}, i.correction.nouveau), " ", i.texte) : h("span", {}, i.texte),
        i.correction ? h("span", { class: "prov corr" }, `ta note du ${dateCourte(i.correction.date)}`) : null)))),
    r.etapes && r.etapes.length ? h("ol", { class: "etapes" }, r.etapes.map(e => h("li", {}, e))) : null)
    : h("section", { class: "cadre" }, h("div", { class: "cadre-tete" }, h("h3", {}, "La recette")),
      h("p", { class: "vide" }, "Pas encore de recette : un lien ou des quantités dans le journal la rempliront."));

  return h("article", { class: "fiche-recette" },
    h("header", { style: "display: flex; flex-direction: column; gap: 8px" },
      h("h2", {}, r.nom),
      h("p", { class: "sous-ligne" }, r.fois ? `Cuisiné ${r.fois} fois · dernière fois le ${dateCourte(r.derniere)}` : "Pas encore cuisinée")),
    lignes.length ? h("section", { class: "fiche", "aria-label": "Fiche" }, lignes) : null,
    cadre,
    r.photos && r.photos.length ? h("section", { class: "section" }, h("h3", {}, "Photos"),
      h("div", { class: "medias", style: "margin-top: 0" }, r.photos.map(p => h("figure", { class: "vignette" },
        h("img", { src: `/${p.fichier}`, alt: p.legende || "photo" }), h("figcaption", {}, `${dateCourte(p.date)} — ${p.legende}`))))) : null,
    r.notes && r.notes.length ? h("section", { class: "section" }, h("h3", {}, "Mes notes"),
      h("ul", { class: "notes" }, r.notes.map(n => h("li", {}, h("span", { class: "date" }, dateCourte(n.date)),
        h("div", {}, n.contexte ? h("span", { class: "ctx" }, n.contexte) : null, h("p", {}, n.texte)))))) : null);
}

// ------------------------------------------------------------------ idées

function vueIdees() {
  const idees = (etat.onglets.idees || {}).idees || [];
  const categorie = i => i.statut === "testee" ? "testees" : (enSaison(i.saison) ? "a_tester" : "hors_saison");
  const compte = c => idees.filter(i => categorie(i) === c).length;
  const filtres = [["a_tester", `À tester · ${compte("a_tester")}`], ["hors_saison", `Hors saison · ${compte("hors_saison")}`], ["testees", `Testées · ${compte("testees")}`], ["tout", "Tout"]];
  const visibles = idees.filter(i => etat.filtreIdees === "tout" || categorie(i) === etat.filtreIdees);
  return [
    titreVue("Idées"),
    bandeauExemple("idees"),
    goutsFoyer(),
    h("div", { class: "filtres", role: "group", "aria-label": "Filtrer les idées" }, filtres.map(([id, lib]) =>
      h("button", { type: "button", class: "bouton-texte", "aria-pressed": String(etat.filtreIdees === id), onclick: () => { etat.filtreIdees = id; afficher(); } }, lib))),
    visibles.length ? h("ul", { class: "idees" }, visibles.map(i => {
      const c = categorie(i);
      return h("li", { class: `idee${c !== "a_tester" ? " passee" : ""}` },
        h("div", { class: "tete" }, h("span", { class: "titre" }, i.titre), h("span", { class: "type" }, i.type || "")),
        h("span", { class: "meta" }, `${i.source} · ${dateCourte(i.date)}`),
        i.saison ? h("span", { class: "meta" }, `saison : ${i.saison.texte}`) : null,
        h("p", {}, i.note),
        h("div", { class: "pied" }, c === "testees" ? "testée → voir dans Recettes" : c === "hors_saison" ? "hors saison" : null));
    })) : h("p", { class: "vide" }, "Rien dans cette catégorie."),
  ];
}

// ------------------------------------------------------------------ ardoise

function vueArdoise() {
  const a = etat.onglets.ardoise || { jours: [], repas_a_prevoir: {} };
  const prefs = a.repas_a_prevoir || {};
  const choix = [["soirs", "Soirs"], ["midis_week_end", "Midis du week-end"], ["midis_semaine", "Midis en semaine"], ["entrees", "Entrées"]];
  const bientot = () => annoncer("Demande à Claude une autre proposition pour ce repas.");
  const enregistrer = async (message) => {
    try {
      etat.onglets.ardoise = await api("/api/ardoise/preferences", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repas_a_prevoir: prefs, contraintes: document.getElementById("envies").value }) });
      etat.onglets.exemples = etat.onglets.exemples.filter(x => x !== "ardoise");
      afficher();
      if (message) annoncer(message);
    } catch (e) { annoncer(`Pas enregistré : ${e.message}`); }
  };
  return [
    titreVue("Ardoise"),
    bandeauExemple("ardoise"),
    h("form", { class: "preferences", onsubmit: e => { e.preventDefault(); enregistrer("C'est noté. Demande à Claude : « propose ma semaine »."); } },
      h("div", { class: "ligne" }, h("span", { class: "etiquette", id: "repas-l" }, "Repas à prévoir"),
        h("div", { class: "filtres", role: "group", "aria-labelledby": "repas-l" }, choix.map(([id, lib]) =>
          h("button", { type: "button", class: "bouton-texte", "aria-pressed": String(!!prefs[id]), onclick: () => { prefs[id] = !prefs[id]; enregistrer(); } }, prefs[id] ? `✓ ${lib}` : lib)))),
      h("div", { class: "ligne" }, h("label", { class: "etiquette", for: "envies" }, "Cette semaine"),
        h("div", { class: "champ" }, h("input", { type: "text", id: "envies", placeholder: "soirs pressés, envies, invités…", value: a.contraintes || "" }),
          h("button", { type: "submit", class: "bouton" }, "Proposer ma semaine")))),
    a.jours && a.jours.length ? h("section", { class: "semaine", "aria-label": "Menus de la semaine" }, h("ul", {}, a.jours.map(j =>
      h("li", { class: "jour-ardoise" }, h("span", { class: "nom-jour" }, j.jour),
        h("div", { class: "repas-jour" }, j.repas.map(r => h("div", { class: "repas" },
          h("span", { class: "moment" }, r.moment),
          h("span", { class: "plats" }, r.entree ? h("span", { class: "entree-plat" }, r.entree) : null, h("span", { class: "plat" }, r.plat), h("span", { class: "dessert" }, r.dessert), r.raison ? h("span", { class: "raison" }, r.raison) : null),
          h("span", { class: "boutons" },
            h("button", { type: "button", class: "bouton-icone", "aria-label": `Autre proposition : ${j.jour} ${r.moment}`, onclick: bientot }, svg(ICONES.autre, 18)),
            h("button", { type: "button", class: "bouton-icone", "aria-label": `Laisser libre : ${j.jour} ${r.moment}`, onclick: bientot }, svg(ICONES.croix, 18)))))))))) : h("p", { class: "vide" }, "Pas encore de semaine proposée."),
  ];
}

// ------------------------------------------------------------------ carte

const NOMS_TYPES = { restaurant: "resto", a_emporter: "à emporter", cafe: "café", marche: "marché", commerce: "commerce" };

function resumeLieu(l) {
  const m = l.mentions || [];
  if (!m.length) return "";
  return `${dateCourte(m[0].date)} · ${m[0].texte}${m.length > 1 ? ` · ${m.length} mentions` : ""}`;
}

function vueCarte() {
  const lieux = (etat.onglets.lieux || {}).lieux || [];
  const filtres = [["tout", "Tout"], ["restaurant", "Restaurants"], ["a_emporter", "À emporter"], ["cafe", "Cafés"], ["marche", "Marchés et commerces"]];
  const groupe = t => (t === "commerce" ? "marche" : t);
  const visibles = lieux.filter(l => etat.filtreLieux === "tout" || groupe(l.type) === etat.filtreLieux);
  return [
    titreVue("Carte"),
    bandeauExemple("lieux"),
    h("div", { class: "filtres", role: "group", "aria-label": "Filtrer les lieux" }, filtres.map(([id, lib]) =>
      h("button", { type: "button", class: "bouton-texte", "aria-pressed": String(etat.filtreLieux === id), onclick: () => { etat.filtreLieux = id; afficher(); } }, lib))),
    h("div", { class: "carte" },
      h("div", { class: "fond-carte" }, "La carte arrivera dans une prochaine version (OpenStreetMap)."),
      h("aside", { class: "liste-lieux", "aria-label": "Lieux" },
        h("h2", { class: "titre-jour" }, `${visibles.length} lieu${visibles.length > 1 ? "x" : ""}`),
        h("ul", {}, visibles.map(l => h("li", {},
          h("span", { class: "tete" }, h("span", { class: "nom" }, l.nom), h("span", { class: "type" }, NOMS_TYPES[l.type] || l.type)),
          h("span", { class: "meta" }, l.resume || resumeLieu(l)),
          l.adresse ? h("span", { class: "meta" }, l.adresse) : null))))),
  ];
}

// ------------------------------------------------------------------ démarrage

async function demarrer() {
  construireNavigation();
  try { await chargerJournal(); }
  catch (e) { annoncer(`Impossible de lire le journal : ${e.message}`); }
  window.addEventListener("hashchange", changerOnglet);
  await changerOnglet();
}

demarrer();
