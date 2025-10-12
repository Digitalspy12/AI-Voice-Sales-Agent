import type { AppConfig } from './lib/types';

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'DD Solution',
  pageTitle: 'Team Kundan',
  pageDescription: 'A voice agent built For Sales Automation ',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '\logo-Bg.png',
  accent: '#002cf2',
  logoDark: '\logo-Bg.png',
  accentDark: '#1fd5f9',
  startButtonText: 'Start ',

  agentName: undefined,
};
