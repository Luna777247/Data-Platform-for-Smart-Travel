import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function EmbeddedDashboard({
    reportUrl,
    title,
    description,
    height = "800px",
    fallbackToExternal = true
}) {
    return (
        <div className="space-y-4">
            {(title || description) && (
                <div className="space-y-1">
                    {title && <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>}
                    {description && <p className="text-muted-foreground">{description}</p>}
                </div>
            )}
            <Card className="overflow-hidden border-2 border-slate-200 shadow-xl">
                <CardContent className="p-0">
                    <iframe
                        src={reportUrl}
                        width="100%"
                        height={height}
                        frameBorder="0"
                        style={{ border: 0 }}
                        allowFullScreen
                        sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
                    ></iframe>
                </CardContent>
            </Card>

            {fallbackToExternal && (
                <div className="flex justify-end">
                    <a
                        href={reportUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                    >
                        Open in new tab ↗
                    </a>
                </div>
            )}
        </div>
    );
}
