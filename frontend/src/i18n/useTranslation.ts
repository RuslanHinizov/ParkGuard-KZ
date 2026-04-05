import { useStore } from '../store/useStore';
import { translations, type TranslationKey } from './translations';

export function useTranslation() {
  const lang = useStore((s) => s.language);
  const dict = translations[lang];

  function t(key: TranslationKey): string {
    return dict[key] ?? key;
  }

  return { t, lang };
}
