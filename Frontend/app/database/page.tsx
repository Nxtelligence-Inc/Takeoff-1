import { NotionLayout } from "@/components/notion-layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Database, Key, Server } from "lucide-react"
import { DatabaseConnectionStatus } from "@/components/database-connection-status"

export default function DatabasePage() {
  return (
    <NotionLayout>
      <div className="max-w-4xl">
        {/* Page header */}
        <div className="mb-8">
          <h1
            className="notion-page-title flex items-center"
            style={{
              fontSize: "30px",
              fontStyle: "normal",
              fontWeight: 605,
              lineHeight: "95%",
              letterSpacing: "-0.04em",
            }}
          >
            <Database className="notion-page-icon h-8 w-8" />
            Database Configuration
          </h1>
          <p className="text-muted-foreground mt-2">Connect to PostgreSQL or Supabase to store and retrieve analyses</p>
        </div>

        {/* Main content */}
        <Tabs defaultValue="postgresql">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="postgresql">PostgreSQL</TabsTrigger>
            <TabsTrigger value="supabase">Supabase</TabsTrigger>
          </TabsList>

          <TabsContent value="postgresql">
            <div className="notion-card">
              <div className="p-4 border-b border-border/60">
                <h2 className="text-lg font-weight-605">PostgreSQL Configuration</h2>
                <p className="text-sm text-muted-foreground">Connect to your PostgreSQL database</p>
              </div>
              <div className="p-4">
                <DatabaseConnectionStatus type="postgresql" />

                <div className="mt-6 grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="pg-host">Host</Label>
                    <div className="flex items-center gap-2">
                      <Server className="h-4 w-4 text-muted-foreground" />
                      <Input id="pg-host" placeholder="localhost" />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="pg-database">Database</Label>
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      <Input id="pg-database" placeholder="foundation_analyzer" />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="pg-user">Username</Label>
                    <Input id="pg-user" placeholder="postgres" />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="pg-password">Password</Label>
                    <div className="flex items-center gap-2">
                      <Key className="h-4 w-4 text-muted-foreground" />
                      <Input id="pg-password" type="password" placeholder="••••••••" />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="pg-port">Port</Label>
                    <Input id="pg-port" placeholder="5432" />
                  </div>
                </div>
              </div>
              <div className="p-4 border-t border-border/60 flex justify-between">
                <Button variant="outline" className="text-muted-foreground">
                  Test Connection
                </Button>
                <Button className="notion-button notion-button-primary">Save Configuration</Button>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="supabase">
            <div className="notion-card">
              <div className="p-4 border-b border-border/60">
                <h2 className="text-lg font-weight-605">Supabase Configuration</h2>
                <p className="text-sm text-muted-foreground">Connect to your Supabase project</p>
              </div>
              <div className="p-4">
                <DatabaseConnectionStatus type="supabase" />

                <div className="mt-6 grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="supabase-url">Supabase URL</Label>
                    <div className="flex items-center gap-2">
                      <Server className="h-4 w-4 text-muted-foreground" />
                      <Input id="supabase-url" placeholder="https://your-project.supabase.co" />
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="supabase-key">Supabase API Key</Label>
                    <div className="flex items-center gap-2">
                      <Key className="h-4 w-4 text-muted-foreground" />
                      <Input id="supabase-key" type="password" placeholder="••••••••" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-4 border-t border-border/60 flex justify-between">
                <Button variant="outline" className="text-muted-foreground">
                  Test Connection
                </Button>
                <Button className="notion-button notion-button-primary">Save Configuration</Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </NotionLayout>
  )
}

