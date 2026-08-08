# The Dispatch — blog.anmolbakshi.com

A static, security-hardened blog in the "dossier" style of
[anmolbakshi.com](https://anmolbakshi.com). No frameworks, no dependencies, no
database — just HTML, CSS, JS.
```
.
├── index.html              
├── feed.xml                 
├── posts.json               
├── 404.html                
├── CNAME                    
├── .nojekyll                
├── posts/                   
├── templates/               
├── assets/                  
└── .github/workflows/       
```

### The auto-detection part

`.github/workflows/build.yml` runs on **every push**: it scans `posts/` for
`.md` files, rebuilds every generated page and commits the changes. You can
therefore also add a post without running anything locally — just drop a
properly formatted `.md` file into `posts/` and push. The site updates itself within a minute or two.

---
© 2026 Anmol Bakshi · Set in Playfair & Plex Mono
