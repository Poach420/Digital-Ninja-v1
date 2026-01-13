import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import api from '../utils/api';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { cn } from '@/lib/utils';
import {
    AlertTriangle,
    ExternalLink,
    Hammer,
    Package,
    Rocket,
    Server,
    ShieldCheck,
    Terminal
} from 'lucide-react';

const STAGES = [
    {
        key: 'provision',
        label: 'Provision',
        description: 'Provisioning environments and allocating build resources.',
        log: 'Allocating compute, reserving domains, and preparing environment variables.',
        icon: Server,
    },
    {
        key: 'security',
        label: 'Security',
        description: 'Hardening secrets, environment policies, and access rules.',
        log: 'Encrypting secrets, syncing .env safeguards, and applying least-privilege roles.',
        icon: ShieldCheck,
    },
    {
        key: 'build',
        label: 'Build',
        description: 'Executing CI build, dependency installs, and automated diagnostics.',
        log: 'Installing dependencies, running build steps, and executing smoke tests.',
        icon: Hammer,
    },
    {
        key: 'bundle',
        label: 'Bundle',
        description: 'Packaging frontend bundles and backend containers for release.',
        log: 'Bundling assets, generating manifests, and embedding release metadata.',
        icon: Package,
    },
    {
        key: 'promote',
        label: 'Promote',
        description: 'Promoting artifacts to edge network and validating health checks.',
        log: 'Promoting build to production, warming caches, and verifying health probes.',
        icon: Rocket,
    },
];

const PLATFORMS = [
    {
        value: 'vercel',
        label: 'Vercel',
        description: 'Best for frontend-first deploys with instant CDN promotion.',
    },
    {
        value: 'netlify',
        label: 'Netlify',
        description: 'JAMStack hosting with automatic asset optimization.',
    },
    {
        value: 'railway',
        label: 'Railway',
        description: 'Provision backend services and keep infra managed for you.',
    },
];

const STATUS_LABEL = {
    pending: 'Queued',
    active: 'Running',
    success: 'Complete',
    error: 'Failed',
};

const STAGE_DURATIONS_MS = [1100, 900, 1200, 950, 1100];
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const statusClasses = {
    pending: 'border-slate-700 bg-slate-900/50 text-slate-400',
    active: 'border-blue-500/70 bg-blue-500/10 text-blue-200 shadow-[0_0_0_1px_rgba(59,130,246,0.2)]',
    success: 'border-emerald-500/70 bg-emerald-500/10 text-emerald-200',
    error: 'border-red-500/70 bg-red-500/10 text-red-200',
};

const logTone = {
    info: 'text-slate-300',
    success: 'text-emerald-300',
    error: 'text-red-300',
};

const DeploymentConsole = ({
    open,
    onOpenChange,
    projectId,
    projectName,
    defaultPlatform = 'vercel',
    onComplete,
}) => {
    const [platform, setPlatform] = useState(defaultPlatform);
    const [stages, setStages] = useState(() => STAGES.map((stage) => ({ ...stage, status: 'pending' })));
    const [logs, setLogs] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState(null);
    const activeIndexRef = useRef(-1);
    const logEndRef = useRef(null);
    const latestPlatform = useRef(defaultPlatform);

    useEffect(() => {
        latestPlatform.current = defaultPlatform;
    }, [defaultPlatform]);

    useEffect(() => {
        if (open) {
            resetConsole();
        }
    }, [open]);

    useEffect(() => {
        setPlatform(latestPlatform.current);
    }, [open]);

    useEffect(() => {
        if (logEndRef.current) {
            logEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    const resetConsole = useCallback(() => {
        setStages(STAGES.map((stage) => ({ ...stage, status: 'pending' })));
        setLogs([]);
        setError('');
        setResult(null);
        activeIndexRef.current = -1;
        setIsRunning(false);
    }, []);

    const addLog = useCallback((message, level = 'info') => {
        setLogs((prev) => [
            ...prev,
            {
                id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                message,
                level,
                timestamp: new Date().toLocaleTimeString(),
            },
        ]);
    }, []);

    const updateStageStatus = useCallback((index, status) => {
        setStages((prev) =>
            prev.map((stage, idx) =>
                idx === index
                    ? { ...stage, status }
                    : stage
            )
        );
    }, []);

    const promoteCompletedStages = useCallback((index) => {
        setStages((prev) =>
            prev.map((stage, idx) =>
                idx < index && stage.status === 'active' ? { ...stage, status: 'success' } : stage
            )
        );
    }, []);

    const deploymentSummary = useMemo(() => {
        if (!result) return null;
        if (result.platform === 'railway') {
            return {
                label: 'Railway service ready',
                value: result.project_id,
                url: result.url,
            };
        }
        return {
            label: 'Live URL',
            value: result.url,
            url: result.url,
        };
    }, [result]);

    // Simulate pipeline stages while waiting for backend deploy completion.
    const runDeployment = useCallback(async () => {
        if (!projectId || isRunning) return;

        setIsRunning(true);
        setError('');
        setResult(null);
        setStages(STAGES.map((stage, idx) => ({ ...stage, status: idx === 0 ? 'active' : 'pending' })));
        addLog(`🚀 Starting deployment for ${projectName || 'project'} on ${platform.toUpperCase()}.`);

        try {
            const deploymentPromise = api.post(`/projects/${projectId}/deploy`, null, {
                params: { platform },
            }).then((res) => res.data);

            let deploymentData = null;
            for (let idx = 0; idx < STAGES.length; idx += 1) {
                activeIndexRef.current = idx;
                if (idx > 0) {
                    promoteCompletedStages(idx);
                    updateStageStatus(idx, 'active');
                }
                addLog(`⏳ ${STAGES[idx].log}`);

                if (idx === STAGES.length - 1) {
                    const [, data] = await Promise.all([
                        wait(STAGE_DURATIONS_MS[idx]),
                        deploymentPromise,
                    ]);
                    deploymentData = data;
                    if (!deploymentData?.success) {
                        const detail = deploymentData?.error || 'Deployment failed';
                        throw new Error(detail);
                    }
                } else {
                    await wait(STAGE_DURATIONS_MS[idx]);
                }

                updateStageStatus(idx, 'success');
            }

            setResult(deploymentData);
            if (deploymentData?.url) {
                addLog(`✅ Deployment ready at ${deploymentData.url}`, 'success');
            } else {
                addLog('✅ Deployment finalized. Check provider dashboard for details.', 'success');
            }
            onComplete?.(deploymentData);
        } catch (err) {
            const message = err?.response?.data?.detail || err?.response?.data?.error || err?.message || 'Deployment failed';
            setError(message);
            addLog(`❌ ${message}`, 'error');
            const failedIdx = activeIndexRef.current >= 0 ? activeIndexRef.current : 0;
            promoteCompletedStages(failedIdx);
            updateStageStatus(failedIdx, 'error');
            setStages((prev) =>
                prev.map((stage, idx) => (idx > failedIdx && stage.status !== 'success' ? { ...stage, status: 'pending' } : stage))
            );
        } finally {
            setIsRunning(false);
        }
    }, [addLog, platform, projectId, projectName, promoteCompletedStages, updateStageStatus, onComplete, isRunning]);

    const handleOpenState = (nextOpen) => {
        if (!nextOpen && isRunning) {
            return;
        }
        onOpenChange?.(nextOpen);
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenState}>
            <DialogContent className="max-w-5xl bg-slate-900 text-white border border-slate-800 shadow-2xl">
                <DialogHeader>
                    <DialogTitle>One-Click Deployment Pipeline</DialogTitle>
                    <DialogDescription className="text-slate-400">
                        Provision, secure, build, bundle, and promote your application in a guided sequence.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-6">
                    <section className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
                        <p className="text-sm text-slate-400 mb-3">Choose deployment target</p>
                        <RadioGroup
                            value={platform}
                            onValueChange={setPlatform}
                            className="grid sm:grid-cols-3 gap-3"
                        >
                            {PLATFORMS.map((option) => (
                                <label
                                    key={option.value}
                                    htmlFor={`platform-${option.value}`}
                                    className={cn(
                                        'flex flex-col gap-2 rounded-lg border p-3 cursor-pointer transition hover:border-blue-400/60',
                                        platform === option.value ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 bg-slate-900'
                                    )}
                                >
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value={option.value} id={`platform-${option.value}`} disabled={isRunning} />
                                        <span className="font-medium text-white">{option.label}</span>
                                    </div>
                                    <p className="text-xs text-slate-400 leading-relaxed">{option.description}</p>
                                </label>
                            ))}
                        </RadioGroup>
                    </section>

                    <section className="grid lg:grid-cols-[2fr,1fr] gap-4">
                        <div className="space-y-3">
                            {stages.map((stage, idx) => {
                                const StageIcon = stage.icon;
                                const badgeTone = stage.status === 'success'
                                    ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-500/40'
                                    : stage.status === 'active'
                                        ? 'bg-blue-500/20 text-blue-100 border border-blue-500/50'
                                        : stage.status === 'error'
                                            ? 'bg-red-500/20 text-red-100 border border-red-500/50'
                                            : 'bg-slate-800 text-slate-300 border border-slate-700';

                                return (
                                    <div
                                        key={stage.key}
                                        className={cn('rounded-lg border p-4 transition', statusClasses[stage.status])}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-700 bg-slate-950">
                                                    <StageIcon className="h-5 w-5" />
                                                </span>
                                                <div>
                                                    <p className="text-xs uppercase tracking-wider text-slate-400">Stage {idx + 1}</p>
                                                    <p className="text-base font-semibold text-white">{stage.label}</p>
                                                </div>
                                            </div>
                                            <Badge className={badgeTone}>{STATUS_LABEL[stage.status]}</Badge>
                                        </div>
                                        <p className="mt-3 text-sm text-slate-300">{stage.description}</p>
                                    </div>
                                );
                            })}
                        </div>

                        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 flex flex-col">
                            <div className="flex items-center gap-2 text-sm font-medium text-white mb-3">
                                <Terminal className="h-4 w-4" />
                                Pipeline Log
                            </div>
                            <ScrollArea className="h-64 rounded-md border border-slate-800 bg-slate-950/70 p-3">
                                <div className="space-y-2 text-sm font-mono">
                                    {logs.length === 0 && (
                                        <p className="text-slate-500">Awaiting deployment run…</p>
                                    )}
                                    {logs.map((entry, idx) => (
                                        <div key={entry.id} className="flex items-start gap-2">
                                            <span className="text-[11px] text-slate-500 pt-[2px] w-16">{entry.timestamp}</span>
                                            <span className={cn('flex-1 whitespace-pre-wrap leading-relaxed', logTone[entry.level] || logTone.info)}>
                                                {entry.message}
                                            </span>
                                            {idx === logs.length - 1 && <span ref={logEndRef} />}
                                        </div>
                                    ))}
                                </div>
                            </ScrollArea>
                        </div>
                    </section>

                    {error && (
                        <div className="flex items-center gap-3 rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-sm text-red-200">
                            <AlertTriangle className="h-4 w-4" />
                            <span>{error}</span>
                        </div>
                    )}

                    {deploymentSummary && (
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 rounded-lg border border-emerald-500/50 bg-emerald-500/10 p-4">
                            <div>
                                <p className="text-sm text-emerald-200">{deploymentSummary.label}</p>
                                <p className="text-base text-white font-semibold break-all">{deploymentSummary.value}</p>
                            </div>
                            {deploymentSummary.url && (
                                <Button
                                    size="sm"
                                    variant="outline"
                                    className="border-emerald-500/60 text-emerald-200 hover:bg-emerald-500/20"
                                    asChild
                                >
                                    <a href={deploymentSummary.url} target="_blank" rel="noreferrer">
                                        <ExternalLink className="h-4 w-4 mr-2" />
                                        Open Deployment
                                    </a>
                                </Button>
                            )}
                        </div>
                    )}
                </div>

                <DialogFooter className="pt-2">
                    <Button
                        variant="outline"
                        className="border-slate-700 text-slate-300"
                        onClick={() => handleOpenState(false)}
                        disabled={isRunning}
                    >
                        Close
                    </Button>
                    <Button
                        className="bg-orange-500 hover:bg-orange-600"
                        onClick={runDeployment}
                        disabled={isRunning}
                    >
                        {isRunning ? 'Deploying…' : 'Deploy Now'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default DeploymentConsole;
