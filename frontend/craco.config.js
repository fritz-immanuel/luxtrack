// craco.config.js
const path = require('path');

const config = {
  disableHotReload: process.env.DISABLE_HOT_RELOAD === 'true',
};

function removeReactRefreshPlugin(plugins = []) {
  return plugins.filter((p) => {
    const name = p && p.constructor && p.constructor.name;
    if (!name) return true;
    // filter out any react-refresh related plugin instances
    if (name === 'ReactRefreshWebpackPlugin' || name.includes('ReactRefresh')) {
      return false;
    }
    return true;
  });
}

function stripReactRefreshBabelFromRule(rule) {
  if (!rule || !rule.use) return rule;
  const uses = Array.isArray(rule.use) ? rule.use : [rule.use];
  uses.forEach((u) => {
    try {
      if (u && u.loader && u.loader.includes('babel-loader') && u.options && Array.isArray(u.options.plugins)) {
        u.options.plugins = u.options.plugins.filter((pl) => {
          if (!pl) return true;
          // plugin can be string or [plugin, options]
          if (typeof pl === 'string') {
            return pl !== 'react-refresh/babel';
          }
          if (Array.isArray(pl) && typeof pl[0] === 'string') {
            return pl[0] !== 'react-refresh/babel';
          }
          // if plugin is a function / require result, compare its name
          if (typeof pl === 'function' && pl.name === 'reactRefreshBabel') return false;
          return true;
        });
      }
    } catch (err) {
      // ignore silently — we don't want build to crash here
    }
  });

  // return same shape expected by webpack
  if (Array.isArray(rule.use)) rule.use = uses;
  else rule.use = uses[0];
  return rule;
}

module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    configure: (webpackConfig) => {
      const isProd = process.env.NODE_ENV === 'production' || config.disableHotReload === true;

      // Remove ReactRefresh plugin instances in production (defensive)
      if (webpackConfig && Array.isArray(webpackConfig.plugins)) {
        webpackConfig.plugins = removeReactRefreshPlugin(webpackConfig.plugins);
      }

      // Ensure babel-loader does not include react-refresh/babel
      if (webpackConfig && webpackConfig.module && Array.isArray(webpackConfig.module.rules)) {
        webpackConfig.module.rules = webpackConfig.module.rules.map((rule) => {
          // Many CRA configs nest loaders in oneOf -> rules, so handle both
          if (rule.oneOf && Array.isArray(rule.oneOf)) {
            rule.oneOf = rule.oneOf.map(stripReactRefreshBabelFromRule);
            return rule;
          }
          return stripReactRefreshBabelFromRule(rule);
        });
      }

      // If explicit disable requested, also turn off HMR/watch
      if (isProd) {
        webpackConfig.watch = false;
        if (webpackConfig.watchOptions) {
          webpackConfig.watchOptions.ignored = /.*/;
        }
      } else {
        webpackConfig.watchOptions = {
          ...(webpackConfig.watchOptions || {}),
          ignored: [
            '**/node_modules/**',
            '**/.git/**',
            '**/build/**',
            '**/dist/**',
            '**/coverage/**',
            '**/public/**',
          ],
        };
      }

      return webpackConfig;
    },
  },
};
