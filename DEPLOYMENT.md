# Deployment Checklist for pycontw2025.scc.tw

## ✅ GitHub Setup

1. **Repository**: https://github.com/scc-tw/pycontw2025
2. **Push your code**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: PyCon TW 2025 Resource Page"
   git branch -M main
   git remote add origin https://github.com/scc-tw/pycontw2025.git
   git push -u origin main
   ```

3. **Enable GitHub Pages**:
   - Go to: Settings → Pages
   - Source: GitHub Actions
   - The workflow will auto-deploy on push to main

## ✅ Cloudflare DNS Configuration

1. **Add CNAME Record**:
   - Type: `CNAME`
   - Name: `pycontw2025`
   - Content: `scc-tw.github.io`
   - Proxy status: ✅ Proxied (orange cloud)
   - TTL: Auto

2. **SSL/TLS Settings**:
   - Go to SSL/TLS → Overview
   - Set encryption mode to: **Full**
   - Enable: **Always Use HTTPS**
   - Enable: **Automatic HTTPS Rewrites**

3. **Page Rules** (Optional):
   - Add rule for: `pycontw2025.scc.tw/*`
   - Settings: Cache Level → Standard
   - Browser Cache TTL → 4 hours

## ✅ Verification Steps

1. **GitHub Actions**: Check workflow runs successfully
   - https://github.com/scc-tw/pycontw2025/actions

2. **GitHub Pages**: Verify deployment
   - https://scc-tw.github.io/pycontw2025/

3. **Custom Domain**: Test access
   - https://pycontw2025.scc.tw/

4. **SSL Certificate**: Verify HTTPS works
   - Check for padlock icon in browser
   - No mixed content warnings

## ✅ Content Management

1. **Add Resources**:
   - Place files in `/public/resources/source/` and `/public/resources/data/`
   - Update `/public/manifest.json` with file paths

2. **Deploy Updates**:
   ```bash
   git add .
   git commit -m "Add benchmark resources"
   git push
   ```
   - GitHub Actions will auto-deploy

## 🚨 Troubleshooting

### Domain Not Working
- Wait 10-15 minutes for DNS propagation
- Check Cloudflare DNS settings
- Verify CNAME file exists in repository

### SSL Issues
- Ensure Cloudflare SSL mode is "Full"
- Clear browser cache
- Wait for certificate provisioning (up to 24 hours)

### Build Failures
- Check GitHub Actions logs
- Verify all dependencies in package.json
- Run `npm run build` locally to test

### 404 Errors
- Ensure base path is `/` in vite.config.ts
- Check router configuration uses hash mode
- Verify CNAME file is in public folder

## 📞 Support

- GitHub Issues: https://github.com/scc-tw/pycontw2025/issues
- Cloudflare Support: https://support.cloudflare.com/