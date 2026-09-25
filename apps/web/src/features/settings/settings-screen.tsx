"use client";

import { PageHeader } from "@/components/page-states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { AuditPanel } from "./audit-panel";
import { BackupPanel } from "./backup-panel";
import { ConfigPanel } from "./config-panel";
import { UsersPanel } from "./users-panel";

export function SettingsScreen() {
  return (
    <div className="space-y-5">
      <PageHeader
        title="Cài đặt hệ thống"
        description="Tài khoản nhân viên, cấu hình chung, nhật ký thao tác và sao lưu dữ liệu."
      />
      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Tài khoản</TabsTrigger>
          <TabsTrigger value="config">Cấu hình</TabsTrigger>
          <TabsTrigger value="audit">Nhật ký thao tác</TabsTrigger>
          <TabsTrigger value="backup">Sao lưu</TabsTrigger>
        </TabsList>
        <TabsContent value="users">
          <UsersPanel />
        </TabsContent>
        <TabsContent value="config">
          <ConfigPanel />
        </TabsContent>
        <TabsContent value="audit">
          <AuditPanel />
        </TabsContent>
        <TabsContent value="backup">
          <BackupPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
