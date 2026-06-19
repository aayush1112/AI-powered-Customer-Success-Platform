"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";

import {
  AuthBrandingPanel,
  AuthFormPanel,
} from "@/components/layouts/AuthShell";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/features/auth";

const PASSWORD_RULES = [
  { label: "At least 8 characters", test: (p: string) => p.length >= 8 },
  { label: "One uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { label: "One lowercase letter", test: (p: string) => /[a-z]/.test(p) },
  { label: "One number", test: (p: string) => /\d/.test(p) },
  {
    label: "One special character",
    test: (p: string) => /[!@#$%^&*()\-_=+[\]{};:'",.<>?/\\|`~]/.test(p),
  },
];

const registerSchema = z.object({
  first_name: z.string().min(1, "First name is required").max(100),
  last_name: z.string().min(1, "Last name is required").max(100),
  email: z.string().email("Please enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .refine((p) => /[A-Z]/.test(p), "Must contain an uppercase letter")
    .refine((p) => /[a-z]/.test(p), "Must contain a lowercase letter")
    .refine((p) => /\d/.test(p), "Must contain a number")
    .refine(
      (p) => /[!@#$%^&*()\-_=+[\]{};:'",.<>?/\\|`~]/.test(p),
      "Must contain a special character"
    ),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { register, isLoading } = useAuth();

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      password: "",
    },
  });

  const password = form.watch("password");

  async function onSubmit(values: RegisterFormValues) {
    try {
      await register(values);
      toast({
        title: "Account created!",
        description: "Please sign in with your new credentials.",
      });
      router.push("/login");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : (err as { data?: { message?: string } })?.data?.message ??
            "Registration failed. Please try again.";
      toast({ variant: "destructive", title: "Registration failed", description: message });
    }
  }

  return (
    <>
      <AuthBrandingPanel
        title="Get started today"
        subtitle="Create your account and start building stronger customer relationships with data-driven insights."
      />
      <AuthFormPanel>
        <Card className="glass-card border-0 shadow-glow">
          <CardHeader className="space-y-1 pb-2">
            <CardTitle className="text-2xl font-bold tracking-tight">
              Create account
            </CardTitle>
            <CardDescription>
              Join your team on the Customer Success Platform
            </CardDescription>
          </CardHeader>

          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <FormField
                    control={form.control}
                    name="first_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>First name</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="John"
                            autoComplete="given-name"
                            disabled={isLoading}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="last_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Last name</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Doe"
                            autoComplete="family-name"
                            disabled={isLoading}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input
                          type="email"
                          placeholder="you@company.com"
                          autoComplete="email"
                          disabled={isLoading}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Password</FormLabel>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder="••••••••"
                          autoComplete="new-password"
                          disabled={isLoading}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />

                      {password.length > 0 && (
                        <ul className="mt-2 space-y-1 rounded-lg bg-muted/50 p-3">
                          {PASSWORD_RULES.map((rule) => {
                            const ok = rule.test(password);
                            return (
                              <li
                                key={rule.label}
                                className={`flex items-center gap-1.5 text-xs ${
                                  ok ? "text-success" : "text-muted-foreground"
                                }`}
                              >
                                {ok ? (
                                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                                ) : (
                                  <XCircle className="h-3.5 w-3.5" />
                                )}
                                {rule.label}
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </FormItem>
                  )}
                />

                <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating account…
                    </>
                  ) : (
                    "Create account"
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>

          <CardFooter className="justify-center border-t border-border/50 pt-4">
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="font-semibold text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </Card>
      </AuthFormPanel>
    </>
  );
}
