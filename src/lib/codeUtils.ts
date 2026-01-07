/**
 * Code formatting utilities
 */

export const formatCode = (code: string, language: string = 'typescript'): string => {
  // In a real implementation, this would use prettier or similar
  // For now, just return the code as-is
  return code.trim();
};

/**
 * Syntax validation
 */
export const validateSyntax = (code: string, language: string = 'typescript'): {
  isValid: boolean;
  errors: string[];
} => {
  // In a real implementation, this would use a proper parser
  const errors: string[] = [];
  
  // Basic checks
  if (!code.trim()) {
    return { isValid: true, errors: [] };
  }
  
  // Check for mismatched brackets
  const openBrackets = (code.match(/\{/g) || []).length;
  const closeBrackets = (code.match(/\}/g) || []).length;
  
  if (openBrackets !== closeBrackets) {
    errors.push('Mismatched curly brackets');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Get language from file extension
 */
export const getLanguageFromExtension = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase();
  
  const languageMap: { [key: string]: string } = {
    'ts': 'typescript',
    'tsx': 'typescript',
    'js': 'javascript',
    'jsx': 'javascript',
    'json': 'json',
    'css': 'css',
    'scss': 'scss',
    'html': 'html',
    'md': 'markdown',
    'py': 'python',
    'java': 'java',
    'go': 'go',
    'rs': 'rust',
  };
  
  return languageMap[ext || ''] || 'text';
};
