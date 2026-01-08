export const isDevAuthEnabled = () => {
  const envFlag = typeof process !== 'undefined' && process.env && process.env.REACT_APP_DEV_AUTH;
  // Enable dev auth on localhost automatically; allow explicit env override too
  return (envFlag === 'true') || (typeof window !== 'undefined' && window.location.hostname === 'localhost');
};

export const devSignIn = ({ email, name }) => {
  const user = {
    user_id: `dev_${Math.random().toString(36).slice(2, 10)}`,
    email: email || 'dev@example.com',
    name: name || 'Dev User',
    created_at: new Date().toISOString(),
    role: 'owner',
    picture: '',
  };
  const token = `dev-token-${Math.random().toString(36).slice(2)}`;
  localStorage.setItem('token', token);
  localStorage.setItem('user', JSON.stringify(user));
  return { token, user };
};