// JSX transform enabled - no React import needed

interface TabsProps {
    activeTab: string
    setActiveTab: (tab: 'dashboard' | 'power' | 'chat' | 'audit') => void
}

export function Tabs({ activeTab, setActiveTab }: TabsProps) {
    const tabs = [
        { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
        { id: 'power', label: '⚡ Power', icon: '⚡' },
        { id: 'chat', label: '💬 Chat', icon: '💬' },
        { id: 'audit', label: '📋 Audit', icon: '📋' },
    ]

    return (
        <div className="bg-slate-900 border-b border-gray-700 px-6">
            <div className="flex gap-0 overflow-x-auto">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`px-4 py-3 font-medium transition-colors border-b-2 whitespace-nowrap ${activeTab === tab.id
                            ? 'border-purple-500 text-purple-400'
                            : 'border-transparent text-gray-400 hover:text-gray-300'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>
        </div>
    )
}// JSX transform enabled - no React import needed

export function Header() {
    return (
        <header className="bg-slate-900 border-b border-purple-900/50 px-6 py-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-lg">🧠</span>
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-100">VX11 Operator</h1>
                        <p className="text-xs text-gray-500">tentacular systems</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-sm text-gray-400">Online</span>
                    </div>
                    <button className="bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 px-3 py-2 rounded-lg text-sm transition border border-purple-600/50">
                        Settings
                    </button>
                </div>
            </div>
        </header>
    );
}

