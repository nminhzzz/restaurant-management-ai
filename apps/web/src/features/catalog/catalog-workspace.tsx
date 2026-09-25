"use client";

import type { ReactNode } from "react";

import { PageHeader } from "@/components/page-states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DishList } from "@/features/catalog/dish-list";
import { GroupList } from "@/features/catalog/group-list";
import { IngredientList } from "@/features/catalog/ingredient-list";
import { SupplierList } from "@/features/catalog/supplier-list";
import { TableList } from "@/features/catalog/table-list";
import { useRole } from "@/features/catalog/use-role";

// Report §3.4.2, Bảng 33: the cashier only reads dishes and table status; the warehouse
// only manages ingredients and suppliers. UX only — the API enforces the same matrix.
const TABS: {
  value: string;
  label: string;
  roles: string[];
  body: ReactNode;
}[] = [
  {
    value: "dishes",
    label: "Món ăn",
    roles: ["MANAGER", "CASHIER"],
    body: <DishList />,
  },
  {
    value: "groups",
    label: "Nhóm món",
    roles: ["MANAGER", "CASHIER"],
    body: <GroupList />,
  },
  {
    value: "ingredients",
    label: "Nguyên liệu",
    roles: ["MANAGER", "WAREHOUSE"],
    body: <IngredientList />,
  },
  {
    value: "suppliers",
    label: "Nhà cung cấp",
    roles: ["MANAGER", "WAREHOUSE"],
    body: <SupplierList />,
  },
  {
    value: "tables",
    label: "Bàn",
    roles: ["MANAGER", "CASHIER"],
    body: <TableList />,
  },
];

export function CatalogWorkspace() {
  const role = useRole();
  const tabs =
    role === null ? TABS : TABS.filter((tab) => tab.roles.includes(role));

  return (
    <div className="space-y-5">
      <PageHeader title="Danh mục" />
      {/* Keyed by role so the first visible tab is selected once the session loads. */}
      <Tabs key={role ?? "anonymous"} defaultValue={tabs[0]?.value}>
        <TabsList>
          {tabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {tabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value}>
            {tab.body}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
